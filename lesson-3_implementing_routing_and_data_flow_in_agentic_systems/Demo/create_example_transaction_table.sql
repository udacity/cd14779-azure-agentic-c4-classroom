CREATE TABLE Example_Transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    account_id NVARCHAR(50) NOT NULL,
    type NVARCHAR(50) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    date DATETIME2 NOT NULL,
    status NVARCHAR(20) NOT NULL,
    description NVARCHAR(MAX)
);