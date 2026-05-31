# Lexi Product Agent — Template

Agente de voz LiveKit para landing pages de suplementos. Clona, configura `.env` y deploya en 5 minutos.

## Cómo clonar para un nuevo producto

```bash
git clone https://github.com/Marte1978/lexi-product-agent.git lexi-NUEVO-PRODUCTO
cd lexi-NUEVO-PRODUCTO
cp .env.example .env
```

Editar `.env` con los datos del producto (ver comentarios en `.env.example`).

## Variables clave a cambiar

| Variable | Ejemplo diabetes | Ejemplo presmin |
|---|---|---|
| `AGENT_NAME` | `lexi-diabetes` | `lexi-presmin` |
| `PRODUCT_NAME` | `Nutresse Diabetes` | `Presmin` |
| `PRODUCT_SPECIALTY` | `diabetes tipo 2` | `prostatitis crónica` |
| `PRODUCT_PRICE` | `RD$2,250` | `RD$2,190` |
| `PRODUCT_URL` | `diabetes.webfactoryrd.com` | `presmin.webfactoryrd.com` |
| `PRODUCT_WHATSAPP` | `809-478-9071` | `809-478-9071` |
| `PRODUCT_INGREDIENTS` | `berberina, cromo, canela` | `palmera enana, zinc` |

## Deploy en VPS

```bash
# En el VPS (Contabo)
mkdir -p /opt/lexi-PRODUCTO
scp -r . root@178.18.247.193:/opt/lexi-PRODUCTO/
ssh root@178.18.247.193
cd /opt/lexi-PRODUCTO
docker build -t lexi-PRODUCTO .
docker run -d --name lexi-PRODUCTO --restart=unless-stopped lexi-PRODUCTO
```

## Conectar con la landing page (campana-candy)

En el endpoint `/api/lexi-PRODUCTO-token/route.ts`, cambiar el `agent_name`:

```typescript
await agentDispatch.createDispatch(roomName, "lexi-PRODUCTO");
```

Y en `AGENT_NAME` del `.env` poner ese mismo valor.

## Voces femeninas disponibles (ElevenLabs)

| Voice ID | Nombre | Estilo |
|---|---|---|
| `hHjbwzYZW17oh0p05AKv` | Default Lexi | Femenina latina, cálida |
| `EXAVITQu4vr4xnSDxMaL` | Sarah | Suave, profesional |
| `XB0fDUnXU5powFXDhCwa` | Charlotte | Cálida, empática |
| `cgSgspJ2msm6clMCkdW1` | Jessica | Conversacional |
