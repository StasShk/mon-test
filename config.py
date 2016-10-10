nginx_config = """
   
    server {{
         listen 80 default_server;
         root /var/www/html;
         index index.php index.html index.htm;
         server_name {};
         charset UTF-8;
        location / {{
         try_files $uri/ /index.php?$args;
         }}
        location ~ \.php$ {{
         try_files $uri =404;
         fastcgi_split_path_info ^(.+\.php)(/.+)$;
         fastcgi_pass unix:/run/php/php7.0-fpm.sock;
         fastcgi_index index.php;
         include fastcgi.conf;
         }}
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|eot|otf|ttf|woff)$ {{
         add_header Access-Control-Allow-Origin *;
         access_log off; log_not_found off; expires 30d;
         }}
        location = /robots.txt {{ access_log off; log_not_found off; }}
         location ~ /\. {{ deny all; access_log off; log_not_found off; }}
        }}

   
     
    """