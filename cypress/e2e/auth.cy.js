describe('Тесты авторизации', () => {
  beforeEach(() => {
    // Очищаем cookies перед каждым тестом
    cy.clearCookies();
  });

  it('Должен отображать форму входа', () => {
    cy.visit('/login/');
    
    cy.get('h1').should('contain', 'Вход');
    cy.get('input[name="username"]').should('be.visible');
    cy.get('input[name="password"]').should('be.visible');
    cy.get('button[type="submit"]').should('contain', 'Войти');
  });

  it('Должен успешно входить с правильными данными', () => {
    cy.visit('/login/');
    
    cy.get('input[name="username"]').type('Manager_Alex');
    cy.get('input[name="password"]').type('qwer1234qwer');
    cy.get('button[type="submit"]').click();
    
    // Проверяем перенаправление на главную страницу
    cy.url().should('not.include', '/login/');
    cy.get('.navbar').should('be.visible');
  });

  it('Должен показывать ошибку с неправильными данными', () => {
    cy.visit('/login/');
    
    cy.get('input[name="username"]').type('wrong_user');
    cy.get('input[name="password"]').type('wrong_password');
    cy.get('button[type="submit"]').click();
    
    // Должны остаться на странице входа
    cy.url().should('include', '/login/');
    
    // Проверяем наличие ошибки (если она отображается)
    cy.get('.text-danger').should('be.visible');
  });

  it('Должен перенаправлять неавторизованных пользователей на страницу входа', () => {
    cy.visit('/vehicles/');
    
    // Должны быть перенаправлены на страницу входа
    cy.url().should('include', '/login/');
  });

  it('Должен позволять выйти из системы', () => {
    // Сначала входим
    cy.login();
    
    // Проверяем, что мы авторизованы
    cy.visit('/vehicles/');
    cy.url().should('not.include', '/login/');
    
    // Выходим (если есть кнопка выхода в интерфейсе)
    cy.get('a[href*="logout"], button').contains('Выйти').click();
    
    // Проверяем, что перенаправлены на страницу входа
    cy.visit('/vehicles/');
    cy.url().should('include', '/login/');
  });
});