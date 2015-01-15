openssl genrsa -des3 -passout pass:x -out server.pass.key 2048
openssl rsa -passin pass:x -in server.pass.key -out server.key
rm server.pass.key

openssl req -new -key server.key -out server.new.csr -nodes -days 1095

openssl x509 -req -in server.new.csr -signkey server.key -out server.new.crt -days 1095

cat server.new.crt server.key > cacert.new.pem