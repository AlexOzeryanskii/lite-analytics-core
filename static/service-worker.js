// Слушаем событие прилета пуш-уведомления от сервера
self.addEventListener('push', function(event) {
    let data = { title: 'Новое уведомление', body: 'У вас новое событие!' };

    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: '/static/icon.png', // Сюда можно будет положить иконку
        badge: '/static/badge.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Клик по уведомлению — открываем нужную страницу
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});