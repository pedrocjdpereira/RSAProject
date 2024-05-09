rm slave-node.tar.gz
rm slave-node/slave-node-image.tar.gz
docker rmi slave-node:latest
docker buildx build -t slave-node slave-node --platform arm64 --load
docker save -o slave-node-image.tar.gz slave-node:latest
mv slave-node-image.tar.gz slave-node
tar -cvzf slave-node.tar.gz slave-node
