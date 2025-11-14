-- Sample transactions for ACC001, ACC002, ACC003
INSERT INTO Example_Transactions (account_id, type, amount, date, status, description)
VALUES 
('ACC001', 'deposit', 1000.00, GETDATE(), 'completed', 'Initial account funding'),
('ACC001', 'withdrawal', 150.50, GETDATE(), 'completed', 'ATM withdrawal'),
('ACC001', 'transfer', 200.00, DATEADD(day, -1, GETDATE()), 'pending', 'Transfer to savings account'),
('ACC002', 'deposit', 500.00, GETDATE(), 'completed', 'Payroll deposit'),
('ACC002', 'purchase', 75.25, DATEADD(hour, -2, GETDATE()), 'completed', 'Online shopping - Amazon'),
('ACC002', 'fee', 5.00, DATEADD(day, -1, GETDATE()), 'completed', 'Monthly service fee'),
('ACC003', 'deposit', 2500.00, GETDATE(), 'completed', 'Bonus payment'),
('ACC003', 'withdrawal', 300.00, DATEADD(hour, -5, GETDATE()), 'completed', 'Cash withdrawal - Branch'),
('ACC003', 'transfer', 500.00, DATEADD(day, -2, GETDATE()), 'completed', 'External transfer to investment account');