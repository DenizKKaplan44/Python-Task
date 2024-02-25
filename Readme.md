 You can install all requirements this way:
    pip install -r requirements.txt

1- The project has 2 runnables
    a) server 
        run :
        uvicorn server:app --reload
    b) client 
       run :
       python client.py --keys gruppe colorCodes labelIds ...
       or 
       python client.py --keys gruppe --no-colored
       or 
       python client.py --help