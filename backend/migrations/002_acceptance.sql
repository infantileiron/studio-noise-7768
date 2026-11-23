CREATE TABLE acceptances (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(80) UNIQUE NOT NULL,
  owner_id INT NOT NULL,
  state ENUM('queued','complete','blocked','failed') NOT NULL DEFAULT 'queued',
  fingerprint CHAR(64) NOT NULL,
  snapshot JSON NOT NULL,
  result JSON,
  reviewer_id INT,
  decision VARCHAR(500),
  reviewed_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  finished_at TIMESTAMP NULL,
  INDEX (state, id),
  FOREIGN KEY (owner_id) REFERENCES accounts(id),
  FOREIGN KEY (reviewer_id) REFERENCES accounts(id)
);
