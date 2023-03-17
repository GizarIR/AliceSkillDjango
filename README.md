# AliceSkillDjango

Steps for start process of developing:
1. pip install -r requirements.txt 
2. Start application: python app.py
3. Start new terminal and start ngrok: ngrok http 8000 
4. Move https address ngrok to option Webhook in your Alice Skill


Steps for start deploy:
1. On VPS <br> ```git clone --branch=deploy-to-vps https://github.com/GizarIR/AliceSkillDjango.git```
2. ```cd AliceSkillDjango/```
3. Move to VPS files credentials by SFTP
4. ```docker-compose build```
4. ```docker-compose up```

For update on VPS:
1. On VPS into AliceSkillFolder folder: ```git pull```
4. ```docker-compose build```
4. ```docker-compose up```