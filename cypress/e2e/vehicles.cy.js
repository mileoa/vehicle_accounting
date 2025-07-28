describe('Управление автомобилями', () => {
  beforeEach(() => {
    // Входим в систему перед каждым тестом
    cy.login();
  });

  describe('Список автомобилей', () => {
    it('Должен отображать список автомобилей', () => {
      cy.visit('/vehicles/');
      
      cy.get('h1').should('contain', 'Автомобили');
      cy.get('table.table').should('be.visible');
      
      // Проверяем заголовки таблицы
      cy.get('table thead th').should('contain', 'Номер машины');
      cy.get('table thead th').should('contain', 'Бренд');
      cy.get('table thead th').should('contain', 'Предприятие');
      cy.get('table thead th').should('contain', 'Цена');
    });

    it('Должен иметь кнопки для создания и экспорта', () => {
      cy.visit('/vehicles/');
      
      cy.get('a[href*="vehicles/create"]').should('contain', 'Создать машину');
      cy.get('a[href*="vehicles/export"]').should('contain', 'Экспорт CSV');
      cy.get('a[href*="vehicles/export/?export_format=json"]').should('contain', 'Экспорт JSON');
    });

    it('Должен отображать пагинацию при наличии множества записей', () => {
      cy.visit('/vehicles/');
      
      // Если есть пагинация, проверяем её
      cy.get('body').then($body => {
        if ($body.find('.pagination').length > 0) {
          cy.get('.pagination').should('be.visible');
        }
      });
    });
  });

  describe('Создание автомобиля', () => {
    it('Должен отображать форму создания автомобиля', () => {
      cy.visit('/vehicles/create/');
      
      cy.get('h1').should('contain', 'Создать машину');
      cy.get('form').should('be.visible');
      
      // Проверяем обязательные поля
      cy.get('input[name="car_number"]').should('be.visible');
      cy.get('input[name="price"]').should('be.visible');
      cy.get('input[name="year_of_manufacture"]').should('be.visible');
      cy.get('input[name="mileage"]').should('be.visible');
      cy.get('select[name="brand"]').should('be.visible');
      cy.get('select[name="enterprise"]').should('be.visible');
    });

    it('Должен создавать новый автомобиль с валидными данными', () => {
      cy.visit('/vehicles/create/');
      
      // Заполняем форму
      const vehicleData = {
        car_number: `${Math.random().toString(36).substr(2, 6).toUpperCase()}`,
        price: '1500000',
        year_of_manufacture: '2020',
        mileage: '50000',
        description: 'Тестовый автомобиль',
        brand: '1', // ID бренда
        enterprise: '1', // ID предприятия
        purchase_datetime: '2023-01-15T10:30'
      };
      
      cy.fillVehicleForm(vehicleData);
      
      // Отправляем форму
      cy.get('button[type="submit"]').contains('Создать').click();
      
      // Проверяем успешное создание
      cy.url().should('include', '/vehicles/');
      cy.checkBootstrapMessage('success', 'успешно создана');
    });

    it('Должен показывать ошибки валидации для невалидных данных', () => {
      cy.visit('/vehicles/create/');
      
      // Пытаемся отправить пустую форму
      cy.get('button[type="submit"]').contains('Создать').click();
      
      // Проверяем, что остались на той же странице
      cy.url().should('include', '/vehicles/create/');
      
    });
  });

  describe('Редактирование автомобиля', () => {
    it('Должен открывать форму редактирования', () => {
      cy.visit('/vehicles/');
      
      // Кликаем на первую доступную ссылку "Изменить"
      cy.get('a').contains('Изменить').first().click();
      
      cy.get('h1').should('contain', 'Изменение машины');
      cy.get('form').should('be.visible');
    });

    it('Должен сохранять изменения', () => {
      cy.visit('/vehicles/');
      
      // Кликаем на первую доступную ссылку "Изменить"
      cy.get('a').contains('Изменить').first().click();
      
      // Изменяем описание
      cy.get('textarea[name="description"]').clear().type('Обновленное описание');
      
      // Сохраняем
      cy.get('button[type="submit"]').contains('Изменить').click();
      
      // Проверяем успешное сохранение
      cy.url().should('include', '/vehicles/');
      cy.checkBootstrapMessage('success', 'успешно изменена');
    });
  });

  describe('Просмотр деталей автомобиля', () => {
    it('Должен отображать детальную информацию об автомобиле', () => {
      cy.visit('/vehicles/');
      
      // Кликаем на первую доступную ссылку "Информация"
      cy.get('a').contains('Информация').first().click();
      
      cy.get('h1').should('contain', 'Информация о машине');
      cy.get('.card').should('be.visible');
      
      // Проверяем наличие основной информации
      cy.get('.card-body').should('contain', 'Цена');
      cy.get('.card-body').should('contain', 'Год выпуска');
      cy.get('.card-body').should('contain', 'Пробег');
      cy.get('.card-body').should('contain', 'Бренд');
      cy.get('.card-body').should('contain', 'Предприятие');
    });

    it('Должен иметь кнопки для управления автомобилем', () => {
      cy.visit('/vehicles/');
      
      // Кликаем на первую доступную ссылку "Информация"
      cy.get('a').contains('Информация').first().click();
      
      // Проверяем наличие кнопок управления
      cy.get('a').contains('Изменить').should('be.visible');
      cy.get('a').contains('Удалить').should('be.visible');
      cy.get('a').contains('Экспорт CSV').should('be.visible');
      cy.get('a').contains('Экспорт JSON').should('be.visible');
    });
  });

  describe('Удаление автомобиля', () => {
    it('Должен показывать подтверждение удаления', () => {
      cy.visit('/vehicles/');
      
      // Кликаем на первую доступную ссылку "Удалить"
      cy.get('a').contains('Удалить').first().click();
      
      cy.get('h1').should('contain', 'Удаление машины');
      cy.get('p').should('contain', 'Вы уверены что хотите удалить');
      cy.get('button[type="submit"]').should('contain', 'Да, удалить');
    });
  });

});