# Guía rápida: WhatsApp Cloud API + ngrok

## Requisitos
- Cuenta en Meta for Developers con acceso a WhatsApp Cloud API
- Bot corriendo en tu máquina local (puerto 8082)
- ngrok instalado ([descargar aquí](https://ngrok.com/download))
- Tokens configurados en `.env`:
  - `WHATSAPP_VERIFY_TOKEN`
  - `WHATSAPP_ACCESS_TOKEN`
  - `WHATSAPP_PHONE_NUMBER_ID`

## Pasos para exponer el webhook con ngrok

1. **Arranca tu bot localmente**
   ```cmd
   py -3 run.py
   ```
   (Asegúrate que el endpoint `/whatsapp/webhook` esté activo)

2. **Ejecuta ngrok para exponer el puerto 8082**
   ```cmd
   ngrok http 8082
   ```
   - ngrok te dará una URL pública HTTPS, por ejemplo: `https://abcd1234.ngrok.io`

3. **Configura el webhook en Meta**
   - Ve a [Meta for Developers](https://developers.facebook.com/apps/)
   - Selecciona tu app de WhatsApp
   - En "Webhooks", agrega la URL pública de ngrok:
     - Ejemplo: `https://abcd1234.ngrok.io/whatsapp/webhook`
   - Usa el mismo `WHATSAPP_VERIFY_TOKEN` que tienes en `.env`

4. **Prueba la conexión**
   - Envía un mensaje desde WhatsApp al número configurado
   - Verifica que tu bot recibe y responde correctamente

## Notas y recomendaciones
- ngrok debe estar corriendo mientras pruebas; cada vez que lo reinicies, la URL pública cambiará.
- Para producción, usa un VPS/servidor con dominio y SSL propio.
- Revisa `docs/whatsapp_setup.md` para detalles avanzados y troubleshooting.

---

¿Dudas? Revisa la documentación oficial o abre un issue en el repo.