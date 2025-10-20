# Despliegue

## Local (Windows)
1) Configura variables en `.env`.
2) Instala dependencias: `pip install -r requirements.txt`.
3) Ejecuta `lanzar_bot.bat` (abre Telegram y API).

## Docker
```bash
docker build -t atencion-cliente .
docker run -p 8082:8082 --env-file .env atencion-cliente
```

## Docker Compose (API + Nginx opcional)
docker-compose.yml (ejemplo):
```yaml
version: '3.9'
services:
	bot:
		build: .
		env_file: .env
		ports:
			- "8082:8082"
	# nginx reverse proxy (opcional, para HTTPS con certbot)
	# nginx:
	#   image: nginx:alpine
	#   volumes:
	#     - ./infra/nginx.conf:/etc/nginx/nginx.conf:ro
	#   ports:
	#     - "80:80"
	#     - "443:443"
	#   depends_on:
	#     - bot
```

## Producción (recomendaciones)
- Coloca Nginx/ALB delante de Uvicorn con HTTPS.
- Usa variables de entorno seguras (no commitees `.env`).
- Observabilidad: health checks, logs centralizados.
- Backups de `config/rules.yaml` y `data/`.
