-- =============================================================================
-- Oracle Library Schema — Execution Context
-- =============================================================================
-- Prerequisites:
--   * Must be run as SYS (or a user with DBA privileges).
--   * Must be executed inside a CDB, targeting the XEPDB1 PDB.
--   * Recommended invocation (from host shell):
--       sqlplus / as sysdba @database/oracle_schema.sql
--     SQL*Plus prompts once for biblioteca_password and reuses it.
-- =============================================================================

SET DEFINE ON
SET SERVEROUTPUT ON
WHENEVER SQLERROR EXIT SQL.SQLCODE

ALTER SESSION SET CONTAINER = XEPDB1;

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM dba_users
    WHERE username = 'BIBLIOTECA';

    -- SQL*Plus prompts for &&biblioteca_password once and defines it for reuse.
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE USER BIBLIOTECA IDENTIFIED BY "&&biblioteca_password" DEFAULT TABLESPACE USERS TEMPORARY TABLESPACE TEMP QUOTA UNLIMITED ON USERS';
        DBMS_OUTPUT.PUT_LINE('Created user BIBLIOTECA.');
    ELSE
        EXECUTE IMMEDIATE 'ALTER USER BIBLIOTECA IDENTIFIED BY "&&biblioteca_password" ACCOUNT UNLOCK';
        EXECUTE IMMEDIATE 'ALTER USER BIBLIOTECA QUOTA UNLIMITED ON USERS';
        DBMS_OUTPUT.PUT_LINE('Updated existing user BIBLIOTECA.');
    END IF;
END;
/

GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE TRIGGER, CREATE VIEW, CREATE PROCEDURE TO BIBLIOTECA;

DECLARE
    PROCEDURE create_table_if_missing(p_table_name IN VARCHAR2, p_sql IN VARCHAR2) IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*)
        INTO v_count
        FROM all_tables
        WHERE owner = 'BIBLIOTECA'
          AND table_name = p_table_name;

        IF v_count = 0 THEN
            EXECUTE IMMEDIATE p_sql;
            DBMS_OUTPUT.PUT_LINE('Created table BIBLIOTECA.' || p_table_name || '.');
        ELSE
            DBMS_OUTPUT.PUT_LINE('Table BIBLIOTECA.' || p_table_name || ' already exists; skipped.');
        END IF;
    END;
BEGIN
    create_table_if_missing('ROLES', q'[
        CREATE TABLE BIBLIOTECA.roles (
            id NUMBER PRIMARY KEY,
            name VARCHAR2(30) NOT NULL UNIQUE,
            description VARCHAR2(255),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
        )
    ]');

    create_table_if_missing('LIBRARY_USERS', q'[
        CREATE TABLE BIBLIOTECA.library_users (
            id NUMBER PRIMARY KEY,
            username VARCHAR2(50) NOT NULL UNIQUE,
            full_name VARCHAR2(120) NOT NULL,
            email VARCHAR2(255) NOT NULL UNIQUE,
            phone VARCHAR2(30),
            password_hash VARCHAR2(255) NOT NULL,
            is_active CHAR(1) DEFAULT 'Y' NOT NULL CHECK (is_active IN ('Y', 'N')),
            role_id NUMBER NOT NULL REFERENCES BIBLIOTECA.roles(id),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
        )
    ]');

    create_table_if_missing('CATEGORIES', q'[
        CREATE TABLE BIBLIOTECA.categories (
            id NUMBER PRIMARY KEY,
            name VARCHAR2(80) NOT NULL UNIQUE,
            description VARCHAR2(500),
            is_active CHAR(1) DEFAULT 'Y' NOT NULL CHECK (is_active IN ('Y', 'N')),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
        )
    ]');

    create_table_if_missing('AUTHORS', q'[
        CREATE TABLE BIBLIOTECA.authors (
            id NUMBER PRIMARY KEY,
            first_name VARCHAR2(80) NOT NULL,
            last_name VARCHAR2(80) NOT NULL,
            biography VARCHAR2(2000),
            birth_date DATE,
            death_date DATE,
            is_active CHAR(1) DEFAULT 'Y' NOT NULL CHECK (is_active IN ('Y', 'N')),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            CONSTRAINT ck_authors_dates CHECK (death_date IS NULL OR birth_date IS NULL OR death_date >= birth_date)
        )
    ]');

    create_table_if_missing('BOOKS', q'[
        CREATE TABLE BIBLIOTECA.books (
            id NUMBER PRIMARY KEY,
            title VARCHAR2(200) NOT NULL,
            isbn VARCHAR2(20) UNIQUE,
            description VARCHAR2(4000),
            publication_date DATE,
            publisher VARCHAR2(120),
            edition VARCHAR2(40),
            pages NUMBER CHECK (pages IS NULL OR pages > 0),
            stock_total NUMBER DEFAULT 0 NOT NULL CHECK (stock_total >= 0),
            stock_available NUMBER DEFAULT 0 NOT NULL CHECK (stock_available >= 0),
            is_active CHAR(1) DEFAULT 'Y' NOT NULL CHECK (is_active IN ('Y', 'N')),
            category_id NUMBER REFERENCES BIBLIOTECA.categories(id),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            CONSTRAINT ck_books_stock CHECK (stock_available <= stock_total)
        )
    ]');

    create_table_if_missing('BOOK_AUTHORS', q'[
        CREATE TABLE BIBLIOTECA.book_authors (
            book_id NUMBER NOT NULL REFERENCES BIBLIOTECA.books(id) ON DELETE CASCADE,
            author_id NUMBER NOT NULL REFERENCES BIBLIOTECA.authors(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            CONSTRAINT pk_book_authors PRIMARY KEY (book_id, author_id)
        )
    ]');

    create_table_if_missing('LOANS', q'[
        CREATE TABLE BIBLIOTECA.loans (
            id NUMBER PRIMARY KEY,
            user_id NUMBER NOT NULL REFERENCES BIBLIOTECA.library_users(id),
            book_id NUMBER NOT NULL REFERENCES BIBLIOTECA.books(id),
            loan_date DATE DEFAULT TRUNC(SYSDATE) NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status VARCHAR2(20) DEFAULT 'ACTIVE' NOT NULL CHECK (status IN ('ACTIVE', 'RETURNED', 'OVERDUE', 'CANCELLED')),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            CONSTRAINT ck_loans_due_date CHECK (due_date >= loan_date),
            CONSTRAINT ck_loans_return_date CHECK (return_date IS NULL OR return_date >= loan_date)
        )
    ]');

    create_table_if_missing('RETURNS', q'[
        CREATE TABLE BIBLIOTECA.returns (
            id NUMBER PRIMARY KEY,
            loan_id NUMBER NOT NULL UNIQUE REFERENCES BIBLIOTECA.loans(id),
            return_date DATE DEFAULT TRUNC(SYSDATE) NOT NULL,
            fine_amount NUMBER(10, 2) DEFAULT 0 NOT NULL CHECK (fine_amount >= 0),
            notes VARCHAR2(1000),
            created_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
        )
    ]');
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_roles_updated_at
BEFORE UPDATE ON BIBLIOTECA.roles
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_library_users_updated_at
BEFORE UPDATE ON BIBLIOTECA.library_users
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_categories_updated_at
BEFORE UPDATE ON BIBLIOTECA.categories
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_authors_updated_at
BEFORE UPDATE ON BIBLIOTECA.authors
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_books_updated_at
BEFORE UPDATE ON BIBLIOTECA.books
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_loans_updated_at
BEFORE UPDATE ON BIBLIOTECA.loans
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_returns_updated_at
BEFORE UPDATE ON BIBLIOTECA.returns
FOR EACH ROW
BEGIN
    :NEW.updated_at := SYSTIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_loans_checkout_stock
BEFORE INSERT ON BIBLIOTECA.loans
FOR EACH ROW
DECLARE
    v_stock_available NUMBER;
BEGIN
    IF :NEW.status IS NULL THEN
        :NEW.status := 'ACTIVE';
    END IF;

    IF :NEW.status = 'ACTIVE' THEN
        SELECT stock_available
        INTO v_stock_available
        FROM BIBLIOTECA.books
        WHERE id = :NEW.book_id
        FOR UPDATE;

        IF v_stock_available <= 0 THEN
            RAISE_APPLICATION_ERROR(-20001, 'Book has no available stock for loan.');
        END IF;

        UPDATE BIBLIOTECA.books
        SET stock_available = stock_available - 1
        WHERE id = :NEW.book_id;
    END IF;
END;
/

CREATE OR REPLACE TRIGGER BIBLIOTECA.trg_returns_restore_stock
AFTER INSERT ON BIBLIOTECA.returns
FOR EACH ROW
DECLARE
    v_book_id BIBLIOTECA.loans.book_id%TYPE;
    v_status BIBLIOTECA.loans.status%TYPE;
BEGIN
    SELECT book_id, status
    INTO v_book_id, v_status
    FROM BIBLIOTECA.loans
    WHERE id = :NEW.loan_id
    FOR UPDATE;

    IF v_status <> 'RETURNED' THEN
        UPDATE BIBLIOTECA.loans
        SET status = 'RETURNED',
            return_date = :NEW.return_date
        WHERE id = :NEW.loan_id;

        UPDATE BIBLIOTECA.books
        SET stock_available = CASE
            WHEN stock_available < stock_total THEN stock_available + 1
            ELSE stock_available
        END
        WHERE id = v_book_id;
    END IF;
END;
/

DECLARE
    PROCEDURE create_index_if_missing(p_index_name IN VARCHAR2, p_sql IN VARCHAR2) IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*)
        INTO v_count
        FROM all_indexes
        WHERE owner = 'BIBLIOTECA'
          AND index_name = p_index_name;

        IF v_count = 0 THEN
            BEGIN
                EXECUTE IMMEDIATE p_sql;
                DBMS_OUTPUT.PUT_LINE('Created index BIBLIOTECA.' || p_index_name || '.');
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE = -1408 THEN
                        DBMS_OUTPUT.PUT_LINE('Index columns for BIBLIOTECA.' || p_index_name || ' are already indexed; skipped.');
                    ELSE
                        RAISE;
                    END IF;
            END;
        ELSE
            DBMS_OUTPUT.PUT_LINE('Index BIBLIOTECA.' || p_index_name || ' already exists; skipped.');
        END IF;
    END;
BEGIN
    create_index_if_missing('IX_BOOKS_TITLE', 'CREATE INDEX BIBLIOTECA.ix_books_title ON BIBLIOTECA.books(title)');
    create_index_if_missing('IX_BOOKS_CATEGORY', 'CREATE INDEX BIBLIOTECA.ix_books_category ON BIBLIOTECA.books(category_id)');
    create_index_if_missing('IX_AUTHORS_NAME', 'CREATE INDEX BIBLIOTECA.ix_authors_name ON BIBLIOTECA.authors(last_name, first_name)');
    create_index_if_missing('IX_USERS_ROLE', 'CREATE INDEX BIBLIOTECA.ix_users_role ON BIBLIOTECA.library_users(role_id)');
    create_index_if_missing('IX_LOANS_USER_STATUS', 'CREATE INDEX BIBLIOTECA.ix_loans_user_status ON BIBLIOTECA.loans(user_id, status)');
    create_index_if_missing('IX_LOANS_BOOK_STATUS', 'CREATE INDEX BIBLIOTECA.ix_loans_book_status ON BIBLIOTECA.loans(book_id, status)');
    create_index_if_missing('IX_RETURNS_LOAN', 'CREATE INDEX BIBLIOTECA.ix_returns_loan ON BIBLIOTECA.returns(loan_id)');
END;
/

-- =============================================================================
-- Sequences (idempotent) — seq_*_id for each aggregate
-- =============================================================================

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_ROLES_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_roles_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_roles_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_roles_id already exists; skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_LIBRARY_USERS_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_library_users_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_library_users_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_library_users_id already exists; skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_CATEGORIES_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_categories_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_categories_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_categories_id already exists; skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_AUTHORS_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_authors_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_authors_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_authors_id already exists; skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_BOOKS_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_books_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_books_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_books_id already exists; skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_LOANS_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_loans_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_loans_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_loans_id already exists; skipped.');
    END IF;
END;
/

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM all_sequences WHERE sequence_owner = 'BIBLIOTECA' AND sequence_name = 'SEQ_RETURNS_ID';
    IF v_count = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE BIBLIOTECA.seq_returns_id START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
        DBMS_OUTPUT.PUT_LINE('Created sequence BIBLIOTECA.seq_returns_id.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('Sequence BIBLIOTECA.seq_returns_id already exists; skipped.');
    END IF;
END;
/

MERGE INTO BIBLIOTECA.roles target
USING (
    SELECT 'Admin' AS name, 'System administrator role.' AS description FROM dual
    UNION ALL
    SELECT 'Usuario' AS name, 'Default library user role.' AS description FROM dual
) source
ON (target.name = source.name)
WHEN NOT MATCHED THEN
    INSERT (id, name, description)
    VALUES (BIBLIOTECA.seq_roles_id.NEXTVAL, source.name, source.description);

COMMIT;

-- =============================================================================
-- PL/SQL Packages
-- =============================================================================

-- -----------------------------------------------------------------------------
-- pkg_roles
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_roles AS
    PROCEDURE p_insert(
        p_name        IN  BIBLIOTECA.roles.name%TYPE,
        p_description IN  BIBLIOTECA.roles.description%TYPE,
        p_id          OUT BIBLIOTECA.roles.id%TYPE
    );
    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.roles.id%TYPE,
        p_name        IN BIBLIOTECA.roles.name%TYPE,
        p_description IN BIBLIOTECA.roles.description%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.roles.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.roles.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
END pkg_roles;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_roles AS

    PROCEDURE p_insert(
        p_name        IN  BIBLIOTECA.roles.name%TYPE,
        p_description IN  BIBLIOTECA.roles.description%TYPE,
        p_id          OUT BIBLIOTECA.roles.id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.roles (id, name, description)
        VALUES (BIBLIOTECA.seq_roles_id.NEXTVAL, p_name, p_description)
        RETURNING id INTO p_id;
    END p_insert;

    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.roles.id%TYPE,
        p_name        IN BIBLIOTECA.roles.name%TYPE,
        p_description IN BIBLIOTECA.roles.description%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.roles
        SET name        = p_name,
            description = p_description
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.roles.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.roles WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.roles.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, name, description, created_at, updated_at
            FROM BIBLIOTECA.roles
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, name, description, created_at, updated_at
            FROM BIBLIOTECA.roles
            ORDER BY id;
    END p_list;

END pkg_roles;
/

-- -----------------------------------------------------------------------------
-- pkg_library_users
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_library_users AS
    PROCEDURE p_insert(
        p_username      IN  BIBLIOTECA.library_users.username%TYPE,
        p_full_name     IN  BIBLIOTECA.library_users.full_name%TYPE,
        p_email         IN  BIBLIOTECA.library_users.email%TYPE,
        p_phone         IN  BIBLIOTECA.library_users.phone%TYPE,
        p_password_hash IN  BIBLIOTECA.library_users.password_hash%TYPE,
        p_is_active     IN  BIBLIOTECA.library_users.is_active%TYPE,
        p_role_id       IN  BIBLIOTECA.library_users.role_id%TYPE,
        p_id            OUT BIBLIOTECA.library_users.id%TYPE
    );
    PROCEDURE p_update(
        p_id            IN BIBLIOTECA.library_users.id%TYPE,
        p_username      IN BIBLIOTECA.library_users.username%TYPE,
        p_full_name     IN BIBLIOTECA.library_users.full_name%TYPE,
        p_email         IN BIBLIOTECA.library_users.email%TYPE,
        p_phone         IN BIBLIOTECA.library_users.phone%TYPE,
        p_password_hash IN BIBLIOTECA.library_users.password_hash%TYPE,
        p_is_active     IN BIBLIOTECA.library_users.is_active%TYPE,
        p_role_id       IN BIBLIOTECA.library_users.role_id%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.library_users.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.library_users.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
END pkg_library_users;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_library_users AS

    PROCEDURE p_insert(
        p_username      IN  BIBLIOTECA.library_users.username%TYPE,
        p_full_name     IN  BIBLIOTECA.library_users.full_name%TYPE,
        p_email         IN  BIBLIOTECA.library_users.email%TYPE,
        p_phone         IN  BIBLIOTECA.library_users.phone%TYPE,
        p_password_hash IN  BIBLIOTECA.library_users.password_hash%TYPE,
        p_is_active     IN  BIBLIOTECA.library_users.is_active%TYPE,
        p_role_id       IN  BIBLIOTECA.library_users.role_id%TYPE,
        p_id            OUT BIBLIOTECA.library_users.id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.library_users (
            id, username, full_name, email, phone, password_hash, is_active, role_id
        ) VALUES (
            BIBLIOTECA.seq_library_users_id.NEXTVAL, p_username, p_full_name, p_email, p_phone, p_password_hash, p_is_active, p_role_id
        )
        RETURNING id INTO p_id;
    END p_insert;

    PROCEDURE p_update(
        p_id            IN BIBLIOTECA.library_users.id%TYPE,
        p_username      IN BIBLIOTECA.library_users.username%TYPE,
        p_full_name     IN BIBLIOTECA.library_users.full_name%TYPE,
        p_email         IN BIBLIOTECA.library_users.email%TYPE,
        p_phone         IN BIBLIOTECA.library_users.phone%TYPE,
        p_password_hash IN BIBLIOTECA.library_users.password_hash%TYPE,
        p_is_active     IN BIBLIOTECA.library_users.is_active%TYPE,
        p_role_id       IN BIBLIOTECA.library_users.role_id%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.library_users
        SET username      = p_username,
            full_name     = p_full_name,
            email         = p_email,
            phone         = p_phone,
            password_hash = p_password_hash,
            is_active     = p_is_active,
            role_id       = p_role_id
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.library_users.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.library_users WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.library_users.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, username, full_name, email, phone,
                   is_active, role_id, created_at, updated_at
            FROM BIBLIOTECA.library_users
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, username, full_name, email, phone,
                   is_active, role_id, created_at, updated_at
            FROM BIBLIOTECA.library_users
            ORDER BY id;
    END p_list;

END pkg_library_users;
/

-- -----------------------------------------------------------------------------
-- pkg_categories
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_categories AS
    PROCEDURE p_insert(
        p_name        IN  BIBLIOTECA.categories.name%TYPE,
        p_description IN  BIBLIOTECA.categories.description%TYPE,
        p_is_active   IN  BIBLIOTECA.categories.is_active%TYPE,
        p_id          OUT BIBLIOTECA.categories.id%TYPE
    );
    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.categories.id%TYPE,
        p_name        IN BIBLIOTECA.categories.name%TYPE,
        p_description IN BIBLIOTECA.categories.description%TYPE,
        p_is_active   IN BIBLIOTECA.categories.is_active%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.categories.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.categories.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
END pkg_categories;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_categories AS

    PROCEDURE p_insert(
        p_name        IN  BIBLIOTECA.categories.name%TYPE,
        p_description IN  BIBLIOTECA.categories.description%TYPE,
        p_is_active   IN  BIBLIOTECA.categories.is_active%TYPE,
        p_id          OUT BIBLIOTECA.categories.id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.categories (id, name, description, is_active)
        VALUES (BIBLIOTECA.seq_categories_id.NEXTVAL, p_name, p_description, p_is_active)
        RETURNING id INTO p_id;
    END p_insert;

    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.categories.id%TYPE,
        p_name        IN BIBLIOTECA.categories.name%TYPE,
        p_description IN BIBLIOTECA.categories.description%TYPE,
        p_is_active   IN BIBLIOTECA.categories.is_active%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.categories
        SET name        = p_name,
            description = p_description,
            is_active   = p_is_active
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.categories.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.categories WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.categories.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, name, description, is_active, created_at, updated_at
            FROM BIBLIOTECA.categories
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, name, description, is_active, created_at, updated_at
            FROM BIBLIOTECA.categories
            ORDER BY id;
    END p_list;

END pkg_categories;
/

-- -----------------------------------------------------------------------------
-- pkg_authors
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_authors AS
    PROCEDURE p_insert(
        p_first_name  IN  BIBLIOTECA.authors.first_name%TYPE,
        p_last_name   IN  BIBLIOTECA.authors.last_name%TYPE,
        p_biography   IN  BIBLIOTECA.authors.biography%TYPE,
        p_birth_date  IN  BIBLIOTECA.authors.birth_date%TYPE,
        p_death_date  IN  BIBLIOTECA.authors.death_date%TYPE,
        p_is_active   IN  BIBLIOTECA.authors.is_active%TYPE,
        p_id          OUT BIBLIOTECA.authors.id%TYPE
    );
    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.authors.id%TYPE,
        p_first_name  IN BIBLIOTECA.authors.first_name%TYPE,
        p_last_name   IN BIBLIOTECA.authors.last_name%TYPE,
        p_biography   IN BIBLIOTECA.authors.biography%TYPE,
        p_birth_date  IN BIBLIOTECA.authors.birth_date%TYPE,
        p_death_date  IN BIBLIOTECA.authors.death_date%TYPE,
        p_is_active   IN BIBLIOTECA.authors.is_active%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.authors.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.authors.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
END pkg_authors;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_authors AS

    PROCEDURE p_insert(
        p_first_name  IN  BIBLIOTECA.authors.first_name%TYPE,
        p_last_name   IN  BIBLIOTECA.authors.last_name%TYPE,
        p_biography   IN  BIBLIOTECA.authors.biography%TYPE,
        p_birth_date  IN  BIBLIOTECA.authors.birth_date%TYPE,
        p_death_date  IN  BIBLIOTECA.authors.death_date%TYPE,
        p_is_active   IN  BIBLIOTECA.authors.is_active%TYPE,
        p_id          OUT BIBLIOTECA.authors.id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.authors (
            id, first_name, last_name, biography, birth_date, death_date, is_active
        ) VALUES (
            BIBLIOTECA.seq_authors_id.NEXTVAL, p_first_name, p_last_name, p_biography, p_birth_date, p_death_date, p_is_active
        )
        RETURNING id INTO p_id;
    END p_insert;

    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.authors.id%TYPE,
        p_first_name  IN BIBLIOTECA.authors.first_name%TYPE,
        p_last_name   IN BIBLIOTECA.authors.last_name%TYPE,
        p_biography   IN BIBLIOTECA.authors.biography%TYPE,
        p_birth_date  IN BIBLIOTECA.authors.birth_date%TYPE,
        p_death_date  IN BIBLIOTECA.authors.death_date%TYPE,
        p_is_active   IN BIBLIOTECA.authors.is_active%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.authors
        SET first_name  = p_first_name,
            last_name   = p_last_name,
            biography   = p_biography,
            birth_date  = p_birth_date,
            death_date  = p_death_date,
            is_active   = p_is_active
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.authors.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.authors WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.authors.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, first_name, last_name, biography, birth_date, death_date,
                   is_active, created_at, updated_at
            FROM BIBLIOTECA.authors
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, first_name, last_name, biography, birth_date, death_date,
                   is_active, created_at, updated_at
            FROM BIBLIOTECA.authors
            ORDER BY id;
    END p_list;

END pkg_authors;
/

-- -----------------------------------------------------------------------------
-- pkg_books
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_books AS
    PROCEDURE p_insert(
        p_title           IN  BIBLIOTECA.books.title%TYPE,
        p_isbn            IN  BIBLIOTECA.books.isbn%TYPE,
        p_description     IN  BIBLIOTECA.books.description%TYPE,
        p_publication_date IN BIBLIOTECA.books.publication_date%TYPE,
        p_publisher       IN  BIBLIOTECA.books.publisher%TYPE,
        p_edition         IN  BIBLIOTECA.books.edition%TYPE,
        p_pages           IN  BIBLIOTECA.books.pages%TYPE,
        p_stock_total     IN  BIBLIOTECA.books.stock_total%TYPE,
        p_stock_available IN  BIBLIOTECA.books.stock_available%TYPE,
        p_is_active       IN  BIBLIOTECA.books.is_active%TYPE,
        p_category_id     IN  BIBLIOTECA.books.category_id%TYPE,
        p_id              OUT BIBLIOTECA.books.id%TYPE
    );
    PROCEDURE p_update(
        p_id              IN BIBLIOTECA.books.id%TYPE,
        p_title           IN BIBLIOTECA.books.title%TYPE,
        p_isbn            IN BIBLIOTECA.books.isbn%TYPE,
        p_description     IN BIBLIOTECA.books.description%TYPE,
        p_publication_date IN BIBLIOTECA.books.publication_date%TYPE,
        p_publisher       IN BIBLIOTECA.books.publisher%TYPE,
        p_edition         IN BIBLIOTECA.books.edition%TYPE,
        p_pages           IN BIBLIOTECA.books.pages%TYPE,
        p_stock_total     IN BIBLIOTECA.books.stock_total%TYPE,
        p_stock_available IN BIBLIOTECA.books.stock_available%TYPE,
        p_is_active       IN BIBLIOTECA.books.is_active%TYPE,
        p_category_id     IN BIBLIOTECA.books.category_id%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.books.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.books.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_add_author(
        p_book_id   IN BIBLIOTECA.book_authors.book_id%TYPE,
        p_author_id IN BIBLIOTECA.book_authors.author_id%TYPE
    );
    PROCEDURE p_remove_author(
        p_book_id   IN BIBLIOTECA.book_authors.book_id%TYPE,
        p_author_id IN BIBLIOTECA.book_authors.author_id%TYPE
    );
    PROCEDURE p_clear_authors(
        p_book_id IN BIBLIOTECA.book_authors.book_id%TYPE
    );
    PROCEDURE p_set_authors(
        p_book_id    IN BIBLIOTECA.book_authors.book_id%TYPE,
        p_author_ids IN SYS.ODCINUMBERLIST
    );
END pkg_books;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_books AS

    PROCEDURE p_insert(
        p_title           IN  BIBLIOTECA.books.title%TYPE,
        p_isbn            IN  BIBLIOTECA.books.isbn%TYPE,
        p_description     IN  BIBLIOTECA.books.description%TYPE,
        p_publication_date IN BIBLIOTECA.books.publication_date%TYPE,
        p_publisher       IN  BIBLIOTECA.books.publisher%TYPE,
        p_edition         IN  BIBLIOTECA.books.edition%TYPE,
        p_pages           IN  BIBLIOTECA.books.pages%TYPE,
        p_stock_total     IN  BIBLIOTECA.books.stock_total%TYPE,
        p_stock_available IN  BIBLIOTECA.books.stock_available%TYPE,
        p_is_active       IN  BIBLIOTECA.books.is_active%TYPE,
        p_category_id     IN  BIBLIOTECA.books.category_id%TYPE,
        p_id              OUT BIBLIOTECA.books.id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.books (
            id, title, isbn, description, publication_date, publisher,
            edition, pages, stock_total, stock_available, is_active, category_id
        ) VALUES (
            BIBLIOTECA.seq_books_id.NEXTVAL, p_title, p_isbn, p_description, p_publication_date, p_publisher,
            p_edition, p_pages, p_stock_total, p_stock_available, p_is_active, p_category_id
        )
        RETURNING id INTO p_id;
    END p_insert;

    PROCEDURE p_update(
        p_id              IN BIBLIOTECA.books.id%TYPE,
        p_title           IN BIBLIOTECA.books.title%TYPE,
        p_isbn            IN BIBLIOTECA.books.isbn%TYPE,
        p_description     IN BIBLIOTECA.books.description%TYPE,
        p_publication_date IN BIBLIOTECA.books.publication_date%TYPE,
        p_publisher       IN BIBLIOTECA.books.publisher%TYPE,
        p_edition         IN BIBLIOTECA.books.edition%TYPE,
        p_pages           IN BIBLIOTECA.books.pages%TYPE,
        p_stock_total     IN BIBLIOTECA.books.stock_total%TYPE,
        p_stock_available IN BIBLIOTECA.books.stock_available%TYPE,
        p_is_active       IN BIBLIOTECA.books.is_active%TYPE,
        p_category_id     IN BIBLIOTECA.books.category_id%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.books
        SET title            = p_title,
            isbn             = p_isbn,
            description      = p_description,
            publication_date = p_publication_date,
            publisher        = p_publisher,
            edition          = p_edition,
            pages            = p_pages,
            stock_total      = p_stock_total,
            stock_available  = p_stock_available,
            is_active        = p_is_active,
            category_id      = p_category_id
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.books.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.books WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.books.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, title, isbn, description, publication_date, publisher,
                   edition, pages, stock_total, stock_available, is_active,
                   category_id, created_at, updated_at
            FROM BIBLIOTECA.books
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, title, isbn, description, publication_date, publisher,
                   edition, pages, stock_total, stock_available, is_active,
                   category_id, created_at, updated_at
            FROM BIBLIOTECA.books
            ORDER BY id;
    END p_list;

    PROCEDURE p_add_author(
        p_book_id   IN BIBLIOTECA.book_authors.book_id%TYPE,
        p_author_id IN BIBLIOTECA.book_authors.author_id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.book_authors (book_id, author_id)
        VALUES (p_book_id, p_author_id);
    EXCEPTION
        WHEN DUP_VAL_ON_INDEX THEN
            NULL; -- ignore duplicate (ORA-00001)
    END p_add_author;

    PROCEDURE p_remove_author(
        p_book_id   IN BIBLIOTECA.book_authors.book_id%TYPE,
        p_author_id IN BIBLIOTECA.book_authors.author_id%TYPE
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.book_authors
        WHERE book_id = p_book_id AND author_id = p_author_id;
    END p_remove_author;

    PROCEDURE p_clear_authors(
        p_book_id IN BIBLIOTECA.book_authors.book_id%TYPE
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.book_authors WHERE book_id = p_book_id;
    END p_clear_authors;

    PROCEDURE p_set_authors(
        p_book_id    IN BIBLIOTECA.book_authors.book_id%TYPE,
        p_author_ids IN SYS.ODCINUMBERLIST
    ) IS
    BEGIN
        p_clear_authors(p_book_id);
        IF p_author_ids IS NOT NULL THEN
            FOR i IN 1 .. p_author_ids.COUNT LOOP
                p_add_author(p_book_id, p_author_ids(i));
            END LOOP;
        END IF;
    END p_set_authors;

END pkg_books;
/

-- -----------------------------------------------------------------------------
-- pkg_loans
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_loans AS
    PROCEDURE p_insert(
        p_user_id   IN  BIBLIOTECA.loans.user_id%TYPE,
        p_book_id   IN  BIBLIOTECA.loans.book_id%TYPE,
        p_loan_date IN  BIBLIOTECA.loans.loan_date%TYPE,
        p_due_date  IN  BIBLIOTECA.loans.due_date%TYPE,
        p_id        OUT BIBLIOTECA.loans.id%TYPE
    );
    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.loans.id%TYPE,
        p_user_id     IN BIBLIOTECA.loans.user_id%TYPE,
        p_book_id     IN BIBLIOTECA.loans.book_id%TYPE,
        p_loan_date   IN BIBLIOTECA.loans.loan_date%TYPE,
        p_due_date    IN BIBLIOTECA.loans.due_date%TYPE,
        p_return_date IN BIBLIOTECA.loans.return_date%TYPE,
        p_status      IN BIBLIOTECA.loans.status%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.loans.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.loans.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_cancel(
        p_id        IN  BIBLIOTECA.loans.id%TYPE,
        p_cancelled OUT NUMBER
    );
END pkg_loans;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_loans AS

    PROCEDURE p_insert(
        p_user_id   IN  BIBLIOTECA.loans.user_id%TYPE,
        p_book_id   IN  BIBLIOTECA.loans.book_id%TYPE,
        p_loan_date IN  BIBLIOTECA.loans.loan_date%TYPE,
        p_due_date  IN  BIBLIOTECA.loans.due_date%TYPE,
        p_id        OUT BIBLIOTECA.loans.id%TYPE
    ) IS
    BEGIN
        INSERT INTO BIBLIOTECA.loans (id, user_id, book_id, loan_date, due_date, status)
        VALUES (
            BIBLIOTECA.seq_loans_id.NEXTVAL, p_user_id, p_book_id, p_loan_date, p_due_date, 'ACTIVE'
        )
        RETURNING id INTO p_id;
    END p_insert;

    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.loans.id%TYPE,
        p_user_id     IN BIBLIOTECA.loans.user_id%TYPE,
        p_book_id     IN BIBLIOTECA.loans.book_id%TYPE,
        p_loan_date   IN BIBLIOTECA.loans.loan_date%TYPE,
        p_due_date    IN BIBLIOTECA.loans.due_date%TYPE,
        p_return_date IN BIBLIOTECA.loans.return_date%TYPE,
        p_status      IN BIBLIOTECA.loans.status%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.loans
        SET user_id     = p_user_id,
            book_id     = p_book_id,
            loan_date   = p_loan_date,
            due_date    = p_due_date,
            return_date = p_return_date,
            status      = p_status
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.loans.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.loans WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.loans.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, user_id, book_id, loan_date, due_date, return_date,
                   status, created_at, updated_at
            FROM BIBLIOTECA.loans
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, user_id, book_id, loan_date, due_date, return_date,
                   status, created_at, updated_at
            FROM BIBLIOTECA.loans
            ORDER BY id;
    END p_list;

    PROCEDURE p_cancel(
        p_id        IN  BIBLIOTECA.loans.id%TYPE,
        p_cancelled OUT NUMBER
    ) IS
        v_book_id BIBLIOTECA.loans.book_id%TYPE;
        v_status  BIBLIOTECA.loans.status%TYPE;
    BEGIN
        SELECT book_id, status
        INTO v_book_id, v_status
        FROM BIBLIOTECA.loans
        WHERE id = p_id
        FOR UPDATE;

        IF v_status IN ('RETURNED', 'CANCELLED') THEN
            RAISE_APPLICATION_ERROR(
                -20002,
                'Cannot cancel loan ' || p_id || ': current status is ' || v_status || '.'
            );
        END IF;

        UPDATE BIBLIOTECA.loans
        SET status = 'CANCELLED'
        WHERE id = p_id;

        UPDATE BIBLIOTECA.books
        SET stock_available = CASE
            WHEN stock_available < stock_total THEN stock_available + 1
            ELSE stock_available
        END
        WHERE id = v_book_id;

        p_cancelled := 1;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            p_cancelled := 0;
    END p_cancel;

END pkg_loans;
/

-- -----------------------------------------------------------------------------
-- pkg_returns
-- -----------------------------------------------------------------------------

CREATE OR REPLACE PACKAGE BIBLIOTECA.pkg_returns AS
    PROCEDURE p_process(
        p_loan_id     IN  BIBLIOTECA.returns.loan_id%TYPE,
        p_return_date IN  BIBLIOTECA.returns.return_date%TYPE,
        p_fine_amount IN  BIBLIOTECA.returns.fine_amount%TYPE,
        p_notes       IN  BIBLIOTECA.returns.notes%TYPE,
        p_id          OUT BIBLIOTECA.returns.id%TYPE
    );
    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.returns.id%TYPE,
        p_loan_id     IN BIBLIOTECA.returns.loan_id%TYPE,
        p_return_date IN BIBLIOTECA.returns.return_date%TYPE,
        p_fine_amount IN BIBLIOTECA.returns.fine_amount%TYPE,
        p_notes       IN BIBLIOTECA.returns.notes%TYPE
    );
    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.returns.id%TYPE,
        p_deleted OUT NUMBER
    );
    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.returns.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    );
    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    );
END pkg_returns;
/

CREATE OR REPLACE PACKAGE BODY BIBLIOTECA.pkg_returns AS

    PROCEDURE p_process(
        p_loan_id     IN  BIBLIOTECA.returns.loan_id%TYPE,
        p_return_date IN  BIBLIOTECA.returns.return_date%TYPE,
        p_fine_amount IN  BIBLIOTECA.returns.fine_amount%TYPE,
        p_notes       IN  BIBLIOTECA.returns.notes%TYPE,
        p_id          OUT BIBLIOTECA.returns.id%TYPE
    ) IS
    BEGIN
        -- INSERT only; trg_returns_restore_stock owns loan status + stock side effects.
        INSERT INTO BIBLIOTECA.returns (id, loan_id, return_date, fine_amount, notes)
        VALUES (
            BIBLIOTECA.seq_returns_id.NEXTVAL, p_loan_id, p_return_date, p_fine_amount, p_notes
        )
        RETURNING id INTO p_id;
    END p_process;

    PROCEDURE p_update(
        p_id          IN BIBLIOTECA.returns.id%TYPE,
        p_loan_id     IN BIBLIOTECA.returns.loan_id%TYPE,
        p_return_date IN BIBLIOTECA.returns.return_date%TYPE,
        p_fine_amount IN BIBLIOTECA.returns.fine_amount%TYPE,
        p_notes       IN BIBLIOTECA.returns.notes%TYPE
    ) IS
    BEGIN
        UPDATE BIBLIOTECA.returns
        SET loan_id     = p_loan_id,
            return_date = p_return_date,
            fine_amount = p_fine_amount,
            notes       = p_notes
        WHERE id = p_id;
    END p_update;

    PROCEDURE p_delete(
        p_id      IN  BIBLIOTECA.returns.id%TYPE,
        p_deleted OUT NUMBER
    ) IS
    BEGIN
        DELETE FROM BIBLIOTECA.returns WHERE id = p_id;
        IF SQL%ROWCOUNT > 0 THEN
            p_deleted := 1;
        ELSE
            p_deleted := 0;
        END IF;
    END p_delete;

    PROCEDURE p_sel_by_id(
        p_id     IN  BIBLIOTECA.returns.id%TYPE,
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, loan_id, return_date, fine_amount, notes, created_at, updated_at
            FROM BIBLIOTECA.returns
            WHERE id = p_id;
    END p_sel_by_id;

    PROCEDURE p_list(
        p_cursor OUT SYS_REFCURSOR
    ) IS
    BEGIN
        OPEN p_cursor FOR
            SELECT id, loan_id, return_date, fine_amount, notes, created_at, updated_at
            FROM BIBLIOTECA.returns
            ORDER BY id;
    END p_list;

END pkg_returns;
/

PROMPT BIBLIOTECA Oracle schema is ready in XEPDB1.
EXIT
