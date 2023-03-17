# AliceSkillDjango

Steps for start process of developing:
1. pip install -r requirements.txt 
2. Start application: python app.py
3. Start new terminal and start ngrok: ngrok http 8000 
4. On Alice dialogs param of BackEnd -> Webhook -> http from ngrok 


Steps for start deploy:
1. On VPS <br> ```git clone --branch=deploy-to-vps https://github.com/GizarIR/AliceSkillDjango.git```
2. ```cd AliceSkillDjango/```
3. Move to VPS files credentials by SFTP
4. ```docker-compose build```
5. ```docker-compose up```
6. On Alice dialogs param of BackEnd -> Webhook -> https://yoursite.here/api/v1/alice/

For update on VPS:
1. On VPS into AliceSkillFolder folder: ```git pull```
2. ```docker-compose build```
3. ```docker-compose up```
4. ```docker-compose down```
