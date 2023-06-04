# DICOM-Node-Query-Retrival
This repository contains implementation of DICOM Query/Retrieve (Q/R) node and DICOM Q/R store node. DICOM Q/R node performs C-FIND operation to search PACS for some DICOM studies & get their attributes (e.g., Study Date, Study Description, etc.). After that, it performs C-MOVE operation to retrieve studies based on the attributes returned by C-FIND. 

When C- MOVE is performed, PACS will send the studies to DICOM Q/R store node. The store node will get these studies & save them. Currently, both nodes only support Mammography (MG) modality.

## Requirements
The code depends on Anaconda version 4.8.3 and Python 3.8. Other versions of Anaconda might work as well because the code uses some of the basic Python modules (e.g., os, datetime, argparse, etc.). Other dependencies are listed in the requirements file.

After installing Anaconda, create an environment as:
```
conda create -n <env_name> python=3.8
```

Then, you can proceed with installing other dependencies as:
```
pip install -r requirements.txt
```

## Run Code
### Q/R Store Node
You can run the store node as:
```
sudo -E env "PATH=$PATH" python DICOM_QR_Store_Node.py
```
We run the code with sudo to make it able to create folders & write files.

The program has five optional parameters. These are:

1. aet_store_node: Application Entity Title (AET) of the store node. Defaults to "AI_STORE_SCP".
2. ip_store_node: IP of store node. Defaults to "0.0.0.0".
3. port_store_node: Port of store node. Defaults to 11123.
4. data_root_path: Path at which data is saved. Defaults to "./data". The program will create the folder if it does not exist.
5. mg_sop_class_uid: DICOM identifier for modality that needs to be saved (e.g., MG, CT, DX, etc.). Defaults to "1.2.840.10008.5.1.4.1.1.1.2" which is SOP Class UID for MG.

### Q/R Node
Q/R node is behind an API endpoint (/api/get_dicoms). You can run it as:
```
python DICOM_QR_Node.py
```
The program has two optional parameters. These are:

1. api_server_ip: IP of API server. Defaults to "0.0.0.0".
2. api_server_port: Port of API server. Defaults to 4004.
        
However, the Q/R node itself has 12 parameters. Four of which are required. The parameters are sent as a POST request to the API endpoint. The parameters are illustrated in the below table:
| Name | Description | Required/Optional | Default Value |
|:-------------|:-------------|:-----:|:-----:|
| scp_aet |Application Entity Title (AET) of the PACS server| Required | - |
| scp_ip | IP of the PACS server | Required | - |
| scp_port | Port of the PACS server | Required | - |
| store_node_aet | AET of our store node. This is the store node we run above. If the default name (AI_STORE_SCP) is used when creating the node, we can use it here. | Required | - |
| scu_aet | AET of the server requesting DICOMs | Optional | "AI_QR" |
| scu_ip | IP of the server requesting DICOMs | Optional | "0.0.0.0" |
| scu_port | Port of the server requesting DICOMs | Optional | 11120 |
| expected_study_description | A string used to get only relevant studies from all returned studies. Relevant studies are the ones containing this string in their study descriptions. | Optional | "" |
| sop_class_uid | DICOM identifier of modality that needs to be retrieved (e.g., MG, CT, DX, etc.) | Optional | "1.2.840.10008.5.1.4.1.1.1.2" which is MG’s UID |
| query_retrieve_level | Tells PACS to send responses as one per study, one per series, one per image | Optional | "SERIES" |
| study_date_range | Date range to be searched | Optional | If a range isn’t provided, then the search will be done on three days that are today and previous two days (e.g., "20230526-20230528") |
| responses_limit | A number that limits how many studies should be retrieved | Optional | -1 (Get all studies) |

As the code places Q/R node behind an API endpoint, you can call the endpoint as:

```python
import requests
import json

# API endpoint details
api_server_ip = "<api_server_ip>"
api_server_port = <api_server_port>
api_endpoint = "/api/get_dicoms"

url = "http://" + api_server_ip + ":" + str(api_server_port) + api_endpoint

# Q/R node parameters
scp_aet = "<scp_aet>"
scp_ip = "<scp_ip>"
scp_port = <scp_port>
store_node_aet = "<store_node_aet>"

data = {
    "scp_aet": scp_aet,
    "scp_ip": scp_ip,
    "scp_port":scp_port,
    "store_node_aet": store_node_aet
}

# send request
headers = {'Content-Type': 'application/json'}
response = requests.post(url, data=json.dumps(data), headers=headers) 
```
