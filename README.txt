step 1: sudo docker compose up --build
step 2: docker exec -it chat_server sh

with in shell:
step 3: rasa train --fixed-model-name mymodel 
step 4: rasa shell --port 5006
