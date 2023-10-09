# DICOM-Node-Query-Retrival
This repository contains implementation of DICOM Query/Retrieve (Q/R) node and DICOM Q/R store node. DICOM Q/R node performs C-FIND operation to search PACS for some DICOM studies & get their attributes (e.g., Study Date, Study Description, etc.). After that, it performs C-MOVE operation to retrieve studies based on the attributes returned by C-FIND. 

When C- MOVE is performed, PACS will send the studies to DICOM Q/R store node. The store node will get these studies & save them. Currently, both nodes only support Mammography (MG) modality.

## Requirements
The code depends on Anaconda version 4.8.3 and Python 3.8. Other versions of Anaconda might work as well because the code uses some of the basic Python modules (e.g., os, datetime, argparse, etc.). Other dependencies are listed in the requirements file.

After installing Anaconda, create an environment as:
```
conda create -n <env_name> python=3.8
```

After that, activate the environment as:
```
conda activate <env_name>
```

Make sure that the activation is successful by checking the current environment.

Then, go to the directory holding the project's files & proceed with installing other dependencies as:
```
pip install -r requirements.txt
```

Finally, run the store node as:
```
sudo -E env "PATH=$PATH" python DICOM_QR_Store_Node.py
```
The store node has some parameters that can be set. However, using the default ones is fine. The parameters are illustrated in the next section.

## Q/R Store Node Parameters
The below table summarizes parameters of the store node:

| Name | Description | Default Value | Comment |
|:-------------|:-------------|:-----:|:-----|
| aet_store_node | Application Entity Title (AET) of the store node | "AI_STORE_SCP" | - |
| ip_store_node | IP of store node | "0.0.0.0" | - |
| port_store_node | Port of store node | 11123 | - |
| data_root_path | Path at which data is saved | "./data"| The program will create the folder if it does not exist |
| mg_sop_class_uid | DICOM identifier for modality that needs to be saved (e.g., MG, CT, DX, etc.) | "1.2.840.10008.5.1.4.1.1.1.2" | This's the SOP Class UID for MG |
