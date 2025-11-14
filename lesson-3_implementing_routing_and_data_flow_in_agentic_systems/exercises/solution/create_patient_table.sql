CREATE TABLE patients (
    patient_id INT PRIMARY KEY,
    name NVARCHAR(100),
    age INT,
    last_visit DATE,
    conditions NVARCHAR(500)
);