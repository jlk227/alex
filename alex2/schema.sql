drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  username text not null,
  email text not null,
  pw_hash text not null
);

-- problem
drop table if exists problem;
create table problem (
  problem_id integer primary key autoincrement,
  level integer not null,
  description text not null,
  func_prefix text not null,
  tests_filename text not null,
  num_users integer default 0,
  num_users_passed integer default 0,
  num_users_failed integer default 0
);

-- user
drop table if exists user_problem_solution;
create table user_problem_solution(
  user_id integer not null,
  problem_id integer not null,
  startedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  submittedAt DATETIME,
  passed boolean default false,
  score real default 0,
  with_study_buddy boolean default false
);

drop table if exists user_test_solution;
create table user_test_solution(
  user_id integer not null,
  problem_id integer not null,
  test_id integer not null,
  passed boolean default false,
  score real default 0,
  with_study_buddy boolean default false
);

drop table if exists user_problem_study_buddy;
create table user_problem_study_buddy(
  id integer primary key autoincrement,
  problem_id integer not null,
  student_id integer not null,
  teacher_id integer,
  createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
  endedAt DATETIME,
  room text not null
);
