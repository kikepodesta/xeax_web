#!/bin/bash
# ---------------------------------------------------------------
# Bootstrap inicial de certificados Let's Encrypt para XEAX Sports.
#
# Nginx no puede arrancar con la config SSL si el certificado no
# existe todavia, asi que:
#   1. Genera un certificado DUMMY autofirmado
#   2. Levanta nginx (ya valida la config)
#   3. Borra el dummy y pide el certificado REAL via webroot
#   4. Recarga nginx
#
# Uso:
#   ./init-letsencrypt.sh           -> certificado real
#   STAGING=1 ./init-letsencrypt.sh -> modo pruebas (sin rate limit)
# ---------------------------------------------------------------
set -e

DOMAINS=(xeaxsports.com www.xeaxsports.com)
EMAIL="admin@xeaxsports.com"   # <-- cambia por un email real de contacto
RSA_KEY_SIZE=4096
STAGING="${STAGING:-0}"

COMPOSE="docker compose -f docker-compose.prod.yml"
CERT_PATH="/etc/letsencrypt/live/${DOMAINS[0]}"

echo "### [1/5] Creando certificado DUMMY para ${DOMAINS[0]} ..."
$COMPOSE run --rm --entrypoint "\
  mkdir -p $CERT_PATH && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '$CERT_PATH/privkey.pem' \
    -out '$CERT_PATH/fullchain.pem' \
    -subj '/CN=localhost'" certbot

echo "### [2/5] Levantando stack (db + web + nginx) ..."
$COMPOSE up -d db web nginx

echo "### [3/5] Eliminando certificado DUMMY ..."
$COMPOSE run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/${DOMAINS[0]} \
         /etc/letsencrypt/archive/${DOMAINS[0]} \
         /etc/letsencrypt/renewal/${DOMAINS[0]}.conf" certbot

DOMAIN_ARGS=""
for d in "${DOMAINS[@]}"; do
  DOMAIN_ARGS="$DOMAIN_ARGS -d $d"
done

STAGING_ARG=""
if [ "$STAGING" = "1" ]; then
  STAGING_ARG="--staging"
  echo "### [4/5] Pidiendo certificado REAL (MODO STAGING) ..."
else
  echo "### [4/5] Pidiendo certificado REAL ..."
fi

$COMPOSE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    $DOMAIN_ARGS \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --no-eff-email" certbot

echo "### [5/5] Recargando nginx ..."
$COMPOSE exec nginx nginx -s reload

echo ""
echo "### Listo. Certificado instalado para: ${DOMAINS[*]}"
echo "### El contenedor 'certbot' renovara automaticamente cada 12h."
