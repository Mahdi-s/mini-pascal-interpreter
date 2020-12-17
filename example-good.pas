program Main;
{Sample Good Test}
procedure Alpha(a : integer; b : integer);
var
x, i: char;
m: real;
w: integer;
j: array [1..10] of integer;
begin {Comment}
   if a = 8  then i := 16;
   while a = 8 do m := 2;
   while a = 0 do writeln('hello');
   if a = 5 then i := 10 else i := 12;
   a := (a + b ) * 2;
   j [1] := 20;
   x := 'g';
   m := 3.5;

end;
begin { Main }
   Alpha(3 + 5, 7);  { procedure call }
   writeln('test');
   write('Hello World');
   read(a);
   readln(x);
end.  { Main }
