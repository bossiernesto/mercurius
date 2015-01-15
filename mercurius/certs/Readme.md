# Create a new Self Signed SSL

| Last Generated |
|----------------|
|  15 Jan, 2015  |

1. Create a new key for generating the CRT and the CSR

    ```Bash
    openssl genrsa -des3 -passout pass:x -out server.pass.key 2048
    openssl rsa -passin pass:x -in server.pass.key -out server.key
    rm server.pass.key
    ```

2. Generate a new CSR

    ```Bash
    openssl req -new -key server.key -out server.new.csr -nodes -days 1095
    ```

3. Generate a new CRT

    ```Bash
    openssl x509 -req -in server.new.csr -signkey server.key -out server.new.crt -days 1095
    ```

4. Concatenate the CRT and the server.key to make the new cacert.new.pem

    ```Bash
    cat server.new.crt server.key > cacert.new.pem
    ```
