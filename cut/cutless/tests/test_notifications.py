from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase, override_settings

from cutless.services.notifications import enviar_notificacion
from cutless.views.optimization import _ejecutar_con_aviso_error, _avisar_sin_piezas


class NotificacionesTests(SimpleTestCase):
    def setUp(self):
        self.perfil = SimpleNamespace(refresh_from_db=lambda: None,
            notificaciones_email=True, notificaciones_pantalla=True,
            email_notificaciones='', notificar_errores=True,
            notificar_optimizacion_completada=True,
            notificar_presupuesto_creado=True, notificar_proyecto_creado=True)
        self.request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True,
            perfil=self.perfil, email='cuenta@example.com', username='persona'))

    @override_settings(EMAIL_HOST='', EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    def test_backend_consola_sin_smtp_se_utiliza(self):
        with patch('sys.stdout', new_callable=StringIO) as output, patch('cutless.services.notifications.messages.success'):
            enviar_notificacion(self.request, 'optimizacion_completada', 'Corte', 'Completado')
            self.assertIn('cuenta@example.com', output.getvalue())

    @override_settings(EMAIL_HOST='', EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_correo_alternativo_y_filtro_por_evento(self):
        self.perfil.email_notificaciones = 'avisos@example.com'
        with patch('cutless.services.notifications.messages.success') as screen:
            enviar_notificacion(self.request, 'proyecto_creado', 'Proyecto', 'Creado')
            self.assertEqual(mail.outbox[-1].to, ['avisos@example.com'])
            self.perfil.notificar_proyecto_creado = False
            enviar_notificacion(self.request, 'proyecto_creado', 'Proyecto', 'Creado')
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(screen.call_count, 1)

    def test_fallo_de_correo_se_registra_sin_propagar(self):
        with patch('cutless.services.notifications.send_mail', side_effect=OSError('fallo simulado')), patch('cutless.services.notifications.messages.success'), self.assertLogs('cutless.services.notifications', level='ERROR'):
            enviar_notificacion(self.request, 'presupuesto_creado', 'Presupuesto', 'Creado')

    def test_canales_apagados_no_envian_avisos(self):
        self.perfil.notificaciones_email = False
        self.perfil.notificaciones_pantalla = False
        with patch('cutless.services.notifications.send_mail') as email, patch('cutless.services.notifications.messages.error') as screen:
            enviar_notificacion(self.request, 'error', 'Error', 'No completado')
            email.assert_not_called()
            screen.assert_not_called()

    def test_error_tecnico_notifica_y_preserva_excepcion(self):
        failure = RuntimeError('fallo de prueba')
        with patch('cutless.views.optimization.enviar_notificacion') as notice:
            with self.assertRaises(RuntimeError):
                _ejecutar_con_aviso_error(self.request, lambda: (_ for _ in ()).throw(failure))
            self.assertEqual(notice.call_args.args[1], 'error')
            self.assertNotIn('fallo de prueba', notice.call_args.args[3])

    def test_explicacion_sin_piezas_no_se_duplica(self):
        with patch('cutless.views.optimization.messages.error') as screen, patch('cutless.views.optimization.enviar_notificacion') as notice:
            _avisar_sin_piezas(self.request, 'No caben las piezas.')
            screen.assert_called_once()
            self.assertFalse(notice.call_args.kwargs['mostrar_en_pantalla'])
