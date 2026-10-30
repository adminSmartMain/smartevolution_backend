-- This database exists only for local QA containers. Django creates and drops
-- test_smartevolution_test, so the test user needs permission to create it.
GRANT ALL PRIVILEGES ON *.* TO 'smartevolution'@'%';
FLUSH PRIVILEGES;
