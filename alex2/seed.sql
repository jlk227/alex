insert into problem (level, description, func_prefix, tests_filename) 
values (1, "
<p>Given an int n, return the absolute difference between n and 21, except return double the absolute difference if n is over 21.</p>

<p>func(19) → 2</p>
<p>func(10) → 11</p>
<p>func(21) → 0</p>", "def func(n):", "problem_1_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (1, "
<p>The parameter weekday is True if it is a weekday, and the parameter vacation is True if we are on vacation. We sleep in if it is not a weekday or we're on vacation. Return True if we sleep in.</p>

<p>func(False, False) → True</p>
<p>func(True, False) → False</p></p>
<p>func(False, True) → True</p>", "def func(weekday, vacation):", "problem_2_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (1, "
<p>Given a string and a non-negative int n, we'll say that the front of the string is the first 3 chars, or whatever is there if the string is less than length 3. Return n copies of the front;</p>

<p>func('Chocolate', 2) → 'ChoCho'</p>
<p>func('Chocolate', 3) → 'ChoChoCho'</p>
<p>func('Abc', 3) → 'AbcAbcAbc'</p>", "def func(str, n):", "problem_3_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (1, "
<p>Given a non-empty string like 'Code' return a string like 'CCoCodCode'.

<p>func('Code') → 'CCoCodCode'</p>
<p>func('abc') → 'aababc'</p>
<p>func('ab') → 'aab'</p>", "def func(str):", "problem_4_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (2, "
<p>Given 2 strings, a and b, return the number of the positions where they contain the same length 2 substring. So 'xxcaazz' and 'xxbaaz' yields 3, since the 'xx', 'aa', and 'az' substrings appear in the same place in both strings.</p>

<p>func('xxcaazz', 'xxbaaz') → 3</p>
<p>func('abc', 'abc') → 2</p>
<p>func('abc', 'axc') → 0</p>", "def func(a, b):", "problem_5_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (2, "
<p>The web is built with HTML strings like '<i>Yay</i>'' which draws Yay as italic text. In this example, the 'i' tag makes <i> and </i> which surround the word 'Yay'. Given tag and word strings, create the HTML string with tags around the word, e.g. '<i>Yay</i>'.</p>

<p>func('i', 'Yay') → '<i>Yay</i>'</p>
<p>func('i', 'Hello') → '<i>Hello</i>'</p>
<p>func('cite', 'Yay') → '<cite>Yay</cite>'</p>", "def func(tag, word):", "problem_6_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (2, "
<p>Given three ints, a b c, return True if one of b or c is 'close' (differing from a by at most 1), while the other is 'far', differing from both other values by 2 or more. Note: abs(num) computes the absolute value of a number.</p>

<p>func(1, 2, 10) → True</p>
<p>func(1, 2, 3) → False</p>
<p>func(4, 1, 3) → True</p>", "def func(a, b, c):", "problem_7_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (2, "
<p>We want make a package of goal kilos of chocolate. We have small bars (1 kilo each) and big bars (5 kilos each). Return the number of small bars to use, assuming we always use big bars before small bars. Return -1 if it can't be done.</p>

<p>func(4, 1, 9) → 4</p>
<p>func(4, 1, 10) → -1</p>
<p>func(4, 1, 7) → 2</p>", "def func(small, big, goal):", "problem_8_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (3, "
<p>Return the number of times that the string 'code' appears anywhere in the given string, except we'll accept any letter for the 'd', so 'cope' and 'cooe' count.</p>

<p>func('aaacodebbb') → 1</p>
<p>func('codexxcode') → 2</p>
<p>func('cozexxcope') → 2</p>", "def func(str):", "problem_9_tests.json");

insert into problem (level, description, func_prefix, tests_filename) 
values (3, "
<p>Return the 'centered' average of an array of ints, which we'll say is the mean average of the values, except ignoring the largest and smallest values in the array. If there are multiple copies of the smallest value, ignore just one copy, and likewise for the largest value. Use int division to produce the final average. You may assume that the array is length 3 or more.</p>

<p>func([1, 2, 3, 4, 100]) → 3</p>
<p>func([1, 1, 5, 5, 10, 8, 7]) → 5</p>
<p>func([-10, -4, -2, -4, -2, 0]) → -3</p>", "def func(nums):", "problem_10_tests.json");
