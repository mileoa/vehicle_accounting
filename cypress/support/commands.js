// Команда для входа в систему
Cypress.Commands.add('login', (username = 'Manager_Alex', password = 'qwer1234qwer') => {
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type(username);
    cy.get('input[name="password"]').type(password);
    cy.get('button[type="submit"]').click();
    
    // Проверяем, что вход успешен
    cy.url().should('not.include', '/login/');
  });

// Команда для выхода из системы
Cypress.Commands.add('logout', () => {
    cy.request('POST', '/accounts/logout/');
  });
  
// Команда для заполнения формы автомобиля
Cypress.Commands.add('fillVehicleForm', (vehicleData) => {
    if (vehicleData.car_number) {
      cy.get('input[name="car_number"]').clear().type(vehicleData.car_number);
    }
    if (vehicleData.price) {
      cy.get('input[name="price"]').clear().type(vehicleData.price.toString());
    }
    if (vehicleData.year_of_manufacture) {
      cy.get('input[name="year_of_manufacture"]').clear().type(vehicleData.year_of_manufacture.toString());
    }
    if (vehicleData.mileage) {
      cy.get('input[name="mileage"]').clear().type(vehicleData.mileage.toString());
    }
    if (vehicleData.description) {
      cy.get('textarea[name="description"]').clear().type(vehicleData.description);
    }
    if (vehicleData.brand) {
      cy.get('select[name="brand"]').select(vehicleData.brand);
    }
    if (vehicleData.enterprise) {
      cy.get('select[name="enterprise"]').select(vehicleData.enterprise);
    }
    if (vehicleData.purchase_datetime) {
      cy.get('input[name="purchase_datetime"]').clear().type(vehicleData.purchase_datetime);
    }
  });

Cypress.Commands.add('checkBootstrapMessage', (type, message) => {
    cy.get(`.alert-${type}`).should('contain', message);
  });
  