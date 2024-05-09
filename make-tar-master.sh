rm master-node.tar.gz
rm master-node/master-node-image.tar.gz
docker rmi master-node:latest
docker buildx build -t master-node master-node --platform arm64 --load
docker save -o master-node-image.tar.gz master-node:latest
mv master-node-image.tar.gz master-node
tar -cvzf master-node.tar.gz master-node
