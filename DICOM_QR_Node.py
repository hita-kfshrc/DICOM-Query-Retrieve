from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind, StudyRootQueryRetrieveInformationModelMove
from pydicom.dataset import Dataset

import os
import time
import datetime
import json
import argparse

from flask import Flask, request, jsonify

"""
This code implements a DICOM QR node. It's divided into two main sections. The first section has four 
    methods to perform Q/R operation. The second section has a Flask API endpoint to easily access
    Q/R node.
"""

app = Flask(__name__)

# log all DICOM connection details
debug_logger()

#### Q/R Methods ####

"""
This method performs C-FIND operation
"""
def c_find(scu_aet, scu_ip, scu_port, scp_aet, scp_ip, scp_port,
            sop_class_uid, study_date_range, query_retrieve_level):
    """
    Input parameters are:
        1. scu_aet: Application Entity Title (AET) of the server requesting DICOMs
        2. scu_ip: IP of the server requesting DICOMs
        3. scu_port: Port of the server requesting DICOMs

        4. scp_aet: AET of the PACS server
        5. scp_ip: IP of the PACS server
        6. scp_port: Port of the PACS server

        7. sop_class_uid: DICOM identifier of modality that needs to be retrieved (e.g., MG, CT, DX, etc.)
        8. study_date_range: Date range to be searched
        9. query_retrieve_level: Tells PACS to send responses as one per study, one per series, one per image

    Outputs are:
        1. returned_studies: A list of retrieved studies
    """

    # build AE
    ae = AE(ae_title=scu_aet)
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

    # build DS
    ds = Dataset()
    ds.SOPClassUID = sop_class_uid
    ds.QueryRetrieveLevel = query_retrieve_level
    ds.StudyDescription = ""
    ds.SeriesDescription = ""
    ds.StudyDate=study_date_range
    ds.AccessionNumber = ""
    ds.PatientID = ""

    # establish association
    assoc = ae.associate(scp_ip, scp_port, ae_title=scp_aet, bind_address=(scu_ip, scu_port))

    # Send C-FIND & loop over responses to collect them
    returned_studies = []
    if assoc.is_established:
        # Send the C-FIND request
        responses = assoc.send_c_find(ds, StudyRootQueryRetrieveInformationModelFind)
        
        for (status, identifier) in responses:
            if status:
                print('C-FIND query status: 0x{0:04X}'.format(status.Status))
                returned_studies.append(identifier)
            else:
                print('Connection timed out, was aborted or received invalid response')

        # Release the association
        assoc.release()
    else:
        print('Association rejected, aborted or never connected')

    # return collected studies
    return returned_studies

"""
A method to get only relevant studies based on their study descriptions. It is needed because some PACS
    return many irrelevant studies even if we include our criteria within C-FIND operation.
"""
def get_relevant_studies(returned_studies, expected_study_description):
    """
    Input parameters are:
        1. returned_studies: A list of studies returned from C-FIND operation
        2. expected_study_description: A string used to get only relevant studies from all returned studies.
            Relevant study are the ones containing this string in their study descriptions.

    Outputs are:
        1. relevant_studies:  A list of relevant studies
    """

    relevant_studies = []
    for returned_study in returned_studies:
        """
        Some studies don't have Study Description attribute. We can ignore those
        """
        try:
            if expected_study_description in returned_study.StudyDescription:
                relevant_studies.append(returned_study)
        except:
            pass

    #relevant_studies = [returned_study for returned_study in returned_studies\
    #                        if expected_study_description in returned_study.StudyDescription]
    return relevant_studies

"""
This method performs C-MOVE operation
"""
def c_move(relevant_studies, scu_aet, scu_ip, scu_port, scp_aet, scp_ip, scp_port,
            store_node_aet, responses_limit):
    """
    Input parameters are:
        1. relevant_studies: A list of relevant studies to be retrieved

        2. scu_aet: Application Entity Title (AET) of the server requesting DICOMs
        3. scu_ip: IP of the server requesting DICOMs
        4. scu_port: Port of the server requesting DICOMs

        5. scp_aet: AET of the PACS server
        6. scp_ip: IP of the PACS server
        7. scp_port: Port of the PACS server

        8. store_node_aet: AET of our store node
        9. responses_limit: A number that limits how many studies should be retrieved
    """
    
    # limit studies list
    if responses_limit == -1:
        relevant_studies = relevant_studies[:len(relevant_studies)]
    else:
        relevant_studies = relevant_studies[:responses_limit]
    
    # loop over studies & request PACS to send them to be stored (C-MOVE)
    for ds in relevant_studies:
        ae = AE(ae_title=scu_aet)
        ae.add_requested_context(StudyRootQueryRetrieveInformationModelMove)

        assoc = ae.associate(scp_ip, scp_port, ae_title=scp_aet, bind_address=(scu_ip, scu_port))

        if assoc.is_established:
            # Use the C-MOVE service to send the identifier
            responses = assoc.send_c_move(ds, store_node_aet, StudyRootQueryRetrieveInformationModelMove)
            for (status, identifier) in responses:
                if status:
                    print('C-MOVE query status: 0x{0:04x}'.format(status.Status))
                else:
                    print('Connection timed out, was aborted or received invalid response')

            # Release the association
            assoc.release()
        else:
            print('Association rejected, aborted or never connected')

        # pause operation between C-MOVE requests to avoid loading PACS
        time.sleep(5)

"""
This method encapsulates the above methods to perform the complete Q/R operation
"""
def DICOM_ops(scu_aet, scu_ip, scu_port, scp_aet, scp_ip, scp_port,
                sop_class_uid, study_date_range, expected_study_description, store_node_aet,
                query_retrieve_level, responses_limit):
    
    # perform C-FIND & get studies
    returned_studies = c_find(scu_aet, scu_ip, scu_port, scp_aet, scp_ip, scp_port,
                                sop_class_uid, study_date_range, query_retrieve_level)

    # get relevant studies
    relevant_studies = get_relevant_studies(returned_studies, expected_study_description)
    
    # C-MOVE
    c_move(relevant_studies, scu_aet, scu_ip, scu_port, scp_aet, scp_ip, scp_port,
            store_node_aet, responses_limit)

    
#### Flask App ####

@app.route('/api/get_dicoms', methods=['POST'])
def get_dicoms():

    dicom_qr_params = request.json

    # check if mandatory parameters are received
    mandatory_params = ["scp_aet", "scp_ip", "scp_port", "store_node_aet"]
    received_params = set(mandatory_params) & set(dicom_qr_params.keys())

    # return error message if at least one of the mandatory parameters is not received
    if len(mandatory_params) != len(received_params):
        missing_params = list(set(mandatory_params) ^ received_params)
        resp = jsonify(response=json.dumps({"Missig Parameters":missing_params}), success=False)
        return resp

    # get mandatory parameters
    scp_aet = dicom_qr_params["scp_aet"]
    scp_ip = dicom_qr_params["scp_ip"]
    scp_port = dicom_qr_params["scp_port"]
    store_node_aet = dicom_qr_params["store_node_aet"]

    # get other parameters
    scu_aet = dicom_qr_params.get("scu_aet", "AI_QR")
    scu_ip = dicom_qr_params.get("scu_ip", "0.0.0.0")
    scu_port = dicom_qr_params.get("scu_port", 11120)
    expected_study_description = dicom_qr_params.get("expected_study_description", "")

    ## if the SOP Class UID isn't provided, it defaults to MG's
    sop_class_uid = dicom_qr_params.get("sop_class_uid", "1.2.840.10008.5.1.4.1.1.1.2")

    query_retrieve_level = dicom_qr_params.get("query_retrieve_level", "SERIES")

    ## if the study date range isn't provided, it defaults to three days that are today and previous two days
    default_study_date_range = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y%m%d") +\
        "-" + datetime.datetime.now().strftime("%Y%m%d")
    study_date_range = dicom_qr_params.get("study_date_range", default_study_date_range)

    responses_limit = dicom_qr_params.get("responses_limit", -1)

    DICOM_ops(scu_aet, scu_ip, scu_port, scp_aet, scp_ip, scp_port,
                sop_class_uid, study_date_range, expected_study_description, store_node_aet,
                query_retrieve_level, responses_limit)

    resp = jsonify(success=True)
    return resp

if __name__ == "__main__":

    # get parameters 
    """
    The parameters are:
        1. api_server_ip: IP of API server
        2. api_server_port: Port of API server
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--api_server_ip", type=str, default="0.0.0.0", help="IP of API server")
    parser.add_argument("--api_server_port", type=int, default=4004, help="Port of API server")

    # parse args
    args = parser.parse_args()

    # get args values
    api_server_ip = args.api_server_ip
    api_server_port = args.api_server_port

    app.run(host=api_server_ip, port=api_server_port, debug=True)
