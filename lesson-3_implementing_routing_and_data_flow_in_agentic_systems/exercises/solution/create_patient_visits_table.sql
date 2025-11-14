CREATE TABLE patient_visits (
    visit_id INT IDENTITY(1,1) PRIMARY KEY,
    patient_name NVARCHAR(100),
    symptoms NVARCHAR(1000),
    diagnosis NVARCHAR(500),
    visit_date DATETIME DEFAULT GETDATE()
);