docker compose down --rmi local
docker rmi -f master-node:latest
docker load -i master-node-image.tar.gz
docker compose up --build
