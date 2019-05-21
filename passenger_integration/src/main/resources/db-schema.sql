


CREATE TABLE passengers (
  PASS_ID INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
  FIRST_NAME VARCHAR(100) NOT NULL,
  LAST_NAME VARCHAR(100) NOT NULL,
  EMAIL VARCHAR(100) NOT NULL,
  IS_BOOKER SMALLINT NOT NULL
);

CREATE TABLE baggage (
  BAG_ID INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
  WEIGHT INTEGER NOT NULL,
  PASS_ID INTEGER not null,
  CONSTRAINT passenger_id_ref FOREIGN KEY (PASS_ID) REFERENCES passengers(PASS_ID)
);
