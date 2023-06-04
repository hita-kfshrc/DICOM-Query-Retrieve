from pynetdicom import AE, evt, debug_logger, build_context
from pynetdicom.sop_class import DigitalMammographyXRayImageStorageForPresentation

import os
import datetime
import time
import argparse

"""
This code implements a DICOM QR store node. It's divided into two main sections. The first section has three 
    methods to handle & save incomming studies and to configure & run DICOM server (node). The second 
    section is the entry point of the program.
"""

#### Utility Methods ####

"""
This method handles incomming DICOM store events. It gets called every time the node recevies 
    a new DICOM store request.
"""
def handle_store(event, data_root_path, mg_sop_class_uid):
    """
    Inputs are:
        1. event: Received event that has incomming DICOMs
        2. data_root_path: Path at which data is saved
        3. mg_sop_class_uid: DICOM identifier for modality that needs to be saved (e.g., MG, CT, DX, etc.)
    """

    # get DICOM dataset (ds) and its SOP Class UID
    ds = event.dataset
    received_sop_class_uid = ds.SOPClassUID

    # check if received ds is MG, 
    """
    Here, we save received ds if it's MG. Otherwise return error code "0xA900" which means
        ds doesn't match expected SOP Class
    """
    if received_sop_class_uid == mg_sop_class_uid:

        # get path at which ds needs to be saved
        data_path = mg_images(data_root_path)
        ds.file_meta = event.file_meta
        ds.save_as(os.path.join(data_path, ds.SOPInstanceUID), write_like_original=False)
        
        return 0x0000
                
    else:
        return 0xA900

"""
A method used to get the right path to store incomming MG studies. It's placed in a separate method to ease
    its expansion. For example, if you'd like to store data of each patient in a separate folder, you
    can have the logic implemented here.
"""
def mg_images(data_path):
    """
    Inputs are:
        1. data_path: Path at which data is saved
    """

    # create folder to save data if it doesn't exist
    if not os.path.isdir(data_path):
        os.mkdir(data_path)
            
    # return path to main folder
    return data_path

"""
This method is used to configure & run store node
"""
def run_qr_store_node(aet_store_node, ip_store_node, port_store_node, data_root_path, mg_sop_class_uid):
    """
    Inputs are:
        1. aet_store_node: Application Entity Title (AET) of the store node
        2. ip_store_node: IP for store node
        3. port_store_node: Port for store node
        4. data_root_path: Path at which data is saved
        5. mg_sop_class_uid: DICOM identifier for modality that needs to be saved (e.g., MG, CT, DX, etc.)
    """

    # event handlers
    handlers = [(evt.EVT_C_STORE, handle_store, [data_root_path, mg_sop_class_uid])]

    # loog DICOM messages
    debug_logger()

    # add MG context to the node
    mg_context = build_context(DigitalMammographyXRayImageStorageForPresentation)

    ae = AE(ae_title=aet_store_node)
    ae_object = ae.start_server((ip_store_node, port_store_node), block=False, evt_handlers=handlers, contexts=[mg_context])

    # make the node always running
    while (True):
        current_time = datetime.datetime.now()
        hour = current_time.hour
        minute = current_time.minute
        day = current_time.strftime("%A")
        day_numeric = current_time.day

        print(day)
        print(hour)
        print(minute)
        print("#####")
        
        time.sleep(60)
    

#### Entry Point ####

if __name__ == "__main__":

    # get parameters 
    """
    The parameters are:
        1. aet_store_node: Application Entity Title (AET) of the store node
        2. ip_store_node: IP of store node
        3. port_store_node: Port of store node
        4. data_root_path: Path at which data is saved
        5. mg_sop_class_uid: DICOM identifier for modality that needs to be saved (e.g., MG, CT, DX, etc.)
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--aet_store_node", type=str, default="AI_STORE_SCP", help="AET of store node")
    parser.add_argument("--ip_store_node", type=str, default="0.0.0.0", help="IP of store node")
    parser.add_argument("--port_store_node", type=int, default=11123, help="Port of store node")
    parser.add_argument("--data_root_path", type=str, default="./data", help="Path at which data is saved")
    parser.add_argument("--mg_sop_class_uid", type=str, default="1.2.840.10008.5.1.4.1.1.1.2",
                    help="DICOM identifier for modality that needs to be saved (e.g., MG, CT, DX, etc.)")

    # parse args
    args = parser.parse_args()

    # get args values
    aet_store_node = args.aet_store_node
    ip_store_node = args.ip_store_node
    port_store_node = args.port_store_node
    data_root_path = args.data_root_path
    mg_sop_class_uid = args.mg_sop_class_uid

    # start store node
    try:
        run_qr_store_node(aet_store_node, ip_store_node, port_store_node, data_root_path, mg_sop_class_uid)

    except Exception as e:
        print("Got the following error: " + str(e))
