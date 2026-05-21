(function() {
    const currentScript = document.currentScript;
    const projectId = currentScript ? currentScript.getAttribute('data-project-id') : null;

    if (!projectId) {
        console.error('LiteAnalytics: data-project-id missing!');
        return;
    }

    const BACKEND_URL = currentScript.getAttribute('data-backend-url') || window.location.origin;

    let sessionId = sessionStorage.getItem('la_session_id');
    if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
        sessionStorage.setItem('la_session_id', sessionId);
    }

    // 1. Отправка аналитики
    function sendEvent(eventType, customPayload = {}) {
        const data = {
            project_id: projectId, session_id: sessionId, event_type: eventType,
            page_url: window.location.href, referrer: document.referrer || 'direct',
            screen_resolution: `${window.screen.width}x${window.screen.height}`, payload: customPayload
        };
        const url = `${BACKEND_URL}/api/track`;
        if (navigator.sendBeacon) {
            navigator.sendBeacon(url, JSON.stringify(data));
        } else {
            fetch(url, { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' }, keepalive: true }).catch(() => {});
        }
    }

    // Авто-запуск аналитики
    if (document.readyState === 'complete') { sendEvent('pageview'); } else { window.addEventListener('load', () => sendEvent('pageview')); }

    // 2. МОДУЛЬ PUSH-УВЕДОМЛЕНИЙ (Регистрация воркера и подписка)
    async function initPushModule() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                // Регистрируем наш сервис-воркер
                const registration = await navigator.serviceWorker.register('/service-worker.js');

                // Запрашиваем у юзера разрешение на пуши
                const permission = await Notification.requestPermission();
                if (permission === 'granted') {
                    // Проверяем, есть ли уже подписка
                    let subscription = await registration.pushManager.getSubscription();

                    if (!subscription) {
                        // Здесь в реальном продакшене нужен VAPID public_key,
                        // пока регистрируем базовую подписку для сбора структуры данных
                        subscription = await registration.pushManager.subscribe({
                            userVisibleOnly: true
                        });
                    }

                    // Отправляем токен устройства на наш бэкенд
                    await fetch(`${BACKEND_URL}/api/push/subscribe`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            project_id: projectId,
                            session_id: sessionId,
                            subscription: subscription
                        })
                    });
                }
            } catch (error) {
                console.log('PushFort: Не удалось активировать пуши (требуется HTTPS в продакшене):', error);
            }
        }
    }

    // Запускаем сбор пуш-токенов через 2 секунды после захода на сайт
    window.addEventListener('load', () => {
        setTimeout(initPushModule, 2000);
    });

    // Трекинг кликов
    document.addEventListener('click', function(e) {
        const target = e.target.closest('.la-click');
        if (target) {
            const eventName = target.getAttribute('data-la-target') || target.innerText || 'click';
            sendEvent('click', { target_name: eventName });
        }
    });
})();