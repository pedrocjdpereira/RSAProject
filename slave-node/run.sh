docker compose down --rmi local
docker rmi -f slave-node:latest
docker load -i slave-node-image.tar.gz
docker compose up --build
