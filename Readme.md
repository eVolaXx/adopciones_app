# Proyecto de portal web de Adopciones caninas. Frontend + Backend.

Se propone desarrollar una plataforma web en Python que permita a protectoras de animales y veterinarios gestionar anuncios de perros en adopción, solicitudes de adopción y seguimiento de cada proceso. La solución incluirá módulos para la gestión de usuarios (adoptantes, personal de refugios y veterinarios), registro de mascotas (con detalles sanitarios), procesos de adopción (solicitud, aprobación, contrato), notificaciones automáticas (email/SMS) e informes de seguimiento. Se priorizarán altos estándares de seguridad y privacidad (cumplimiento RGPD), rendimiento razonable y escalabilidad, así como accesibilidad web (WCAG) y capacidad de internacionalización (soporte multiidioma).

Aquí arquitectura general en capas:
  - Capa de clientes navegador web/movil: Protectoras, veterinarios y familias adoptantes. 
  - Frontend: React + Vite: Portal de adopciones, dashboard admin, ficha animal, estado en tiempo real. 
  - Backend: FastApi Python: Rest Api, websockets, auth JWT, logica de negocio. 
        -Redis(Cache, pub, sub), PostgresSQL(Datos principales), Cloudinary(Fotos animales):
        - Infraestructura: Docker,nginx, railway/vps, sendgrid(emails),Let´s script(SSL)

Aquí el flujo de desarrollo lógico en 5 fases:
    -Fase 1: BD + Auth JWT
    -Fase 2: Api Rest CRUD
    -Fase 3: Websockets Tiempo real
    -Fase 4: Frontend React
    -Fase 5: Docker + Despliegue.
  

# Copyright By Juan Carlos Gil