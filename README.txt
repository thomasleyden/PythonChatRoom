How to run the client:

Example of running the server:
java -cp ChatSystem.jar server.YMemD 8000

Example of running client:
python YaChatClient.py Brian 127.0.0.1 8000
python YaChatClient.py Thomas 127.0.0.1 8000
python YaChatClient.py SuperLongNameUserExtraInformation 127.0.0.1 8000
python YaChatClient.py SuperLongNameUserExtraInformation localhost 8000

Invalid methods of running client
python YaChatClient.py user with spaces localhost 8000
python YaChatClient.py Thomas invalidIp:00:00 8000
python YaChatClient.py Thomas invalidIp:00:00 randomPortString