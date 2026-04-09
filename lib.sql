-- Active: 1775671271620@@localhost@3306@library_db
-- Complete Library Management System SQL Script

DROP DATABASE IF EXISTS library_db;
CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

-- ----------------------------
-- Table: library
-- ----------------------------
CREATE TABLE `library` (
  `Library_ID` int NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Location` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Library_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `library` VALUES 
(1,'Central Library','Main Street, City Center'),
(2,'West Branch','West Avenue, Suburbia'),
(3,'East Branch','East Boulevard, Suburbia');

-- ----------------------------
-- Table: publisher
-- ----------------------------
CREATE TABLE `publisher` (
  `Publisher_ID` int NOT NULL,
  `Name` varchar(255) DEFAULT NULL,
  `Block_No` varchar(10) DEFAULT NULL,
  `Street` varchar(255) DEFAULT NULL,
  `City` varchar(255) DEFAULT NULL,
  `Pincode` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`Publisher_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `publisher` VALUES 
(1,'ABC Publications','Block A','Main Street','City Center','12345'),
(2,'XYZ Books','Block B','West Avenue','Suburbia','54321'),
(3,'TechPress','Block C','East Boulevard','Suburbia','98765');

-- ----------------------------
-- Table: book
-- ----------------------------
CREATE TABLE `book` (
  `ISBN_Number` varchar(13) NOT NULL,
  `Author` varchar(255) NOT NULL,
  `Book_Title` varchar(255) NOT NULL,
  `Language` varchar(50) NOT NULL,
  `genre` varchar(255) DEFAULT NULL,
  `Publisher_ID` int DEFAULT NULL,
  `library_id` int DEFAULT NULL,
  PRIMARY KEY (`ISBN_Number`),
  CONSTRAINT `fk_publisher` FOREIGN KEY (`Publisher_ID`) REFERENCES `publisher` (`Publisher_ID`) ON DELETE SET NULL,
  CONSTRAINT `fk_book_library` FOREIGN KEY (`library_id`) REFERENCES `library` (`Library_ID`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table: book_copies
-- ----------------------------
CREATE TABLE `book_copies` (
  `ISBN_Number` varchar(13) NOT NULL,
  `number_available` int DEFAULT 0,
  PRIMARY KEY (`ISBN_Number`),
  CONSTRAINT `fk_copies_isbn` FOREIGN KEY (`ISBN_Number`) REFERENCES `book` (`ISBN_Number`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table: member
-- ----------------------------
CREATE TABLE `member` (
  `Member_ID` int NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Email` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`Member_ID`),
  UNIQUE KEY `Email` (`Email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `member` VALUES 
(1,'John Smith','john.smith@example.com'),
(2,'Alice Johnson','alice.johnson@example.com');

-- ----------------------------
-- Table: borrow
-- ----------------------------
CREATE TABLE `borrow` (
  `ISBN_Number` varchar(13) NOT NULL,
  `Member_ID` int NOT NULL,
  `Return_Date` date DEFAULT NULL,
  `Due_Date` date DEFAULT NULL,
  `Fine` decimal(10,2) DEFAULT 0.00,
  `date_lent` date DEFAULT NULL,
  PRIMARY KEY (`ISBN_Number`,`Member_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table: staff
-- ----------------------------
CREATE TABLE `staff` (
  `Employee_ID` int NOT NULL,
  `Name` varchar(255) DEFAULT NULL,
  `Designation` varchar(255) DEFAULT NULL,
  `Contact_Number` varchar(20) DEFAULT NULL,
  `Email` varchar(255) DEFAULT NULL,
  `library_id` int DEFAULT NULL,
  PRIMARY KEY (`Employee_ID`),
  CONSTRAINT `fk_staff_library` FOREIGN KEY (`library_id`) REFERENCES `library` (`Library_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `staff` VALUES (101,'Vandhana','Librarian','999-888-7777','vandhana@library.com',1);

-- ----------------------------
-- PROCEDURES
-- ----------------------------
DELIMITER ;;

-- Procedure to Add a Book and its Initial Copies
CREATE PROCEDURE `AddNewBook`(
    IN p_ISBN VARCHAR(13),
    IN p_Author VARCHAR(255),
    IN p_Title VARCHAR(255),
    IN p_Language VARCHAR(50),
    IN p_Genre VARCHAR(255),
    IN p_Publisher_ID INT,
    IN p_Library_ID INT,
    IN p_Copies INT
)
BEGIN
    INSERT INTO book (ISBN_Number, Author, Book_Title, Language, genre, Publisher_ID, library_id)
    VALUES (p_ISBN, p_Author, p_Title, p_Language, p_Genre, p_Publisher_ID, p_Library_ID);

    INSERT INTO book_copies (ISBN_Number, number_available)
    VALUES (p_ISBN, p_Copies);
END;;

-- Procedure to Lend a Book (Decrements count)
CREATE PROCEDURE `LendBook`(
    IN p_ISBN VARCHAR(13),
    IN p_Member_ID INT
)
BEGIN
    DECLARE available INT;
    SELECT number_available INTO available FROM book_copies WHERE ISBN_Number = p_ISBN;

    IF available > 0 THEN
        INSERT INTO borrow (ISBN_Number, Member_ID, Due_Date, date_lent)
        VALUES (p_ISBN, p_Member_ID, DATE_ADD(CURDATE(), INTERVAL 14 DAY), CURDATE());
        
        UPDATE book_copies SET number_available = number_available - 1 WHERE ISBN_Number = p_ISBN;
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No copies available.';
    END IF;
END;;

-- Procedure to Return a Book (Increments count & triggers fine calculation)
CREATE PROCEDURE `ReturnBook`(
    IN p_ISBN VARCHAR(13),
    IN p_Member_ID INT,
    IN p_Return_Date DATE
)
BEGIN
    UPDATE borrow SET Return_Date = p_Return_Date WHERE ISBN_Number = p_ISBN AND Member_ID = p_Member_ID;
    UPDATE book_copies SET number_available = number_available + 1 WHERE ISBN_Number = p_ISBN;
END;;

-- Procedure to Delete a Book (Cleanup all related records)
CREATE PROCEDURE `DeleteBook`(IN p_ISBN VARCHAR(13))
BEGIN
    DELETE FROM book_copies WHERE ISBN_Number = p_ISBN;
    DELETE FROM borrow WHERE ISBN_Number = p_ISBN;
    DELETE FROM book WHERE ISBN_Number = p_ISBN;
END;;

DELIMITER ;

-- ----------------------------
-- Fine Calculation Trigger
-- ----------------------------
DELIMITER ;;
CREATE TRIGGER `CalculateFineTrigger` BEFORE UPDATE ON `borrow` FOR EACH ROW BEGIN
    DECLARE fine_days INT;
    IF NEW.Return_Date > OLD.Due_Date THEN
        SET fine_days = DATEDIFF(NEW.Return_Date, OLD.Due_Date);
        SET NEW.Fine = fine_days * 10.00; -- 10 rupees per day
    END IF;
END;;
DELIMITER ;