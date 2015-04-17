declare
  oldval number(10);
  newval number(10);
  sqlStr varchar2(300);
begin
  oldval := 10000;
  newval := 10000;

  for octime in (select 'to_date(''' ||
                        to_char(occur_time, 'yyyy-mm-dd hh24:mi:ss') ||
                        ''', ''yyyy-mm-dd hh24:mi:ss'')' occur_time
                   from dd_hs_0002
                  where occur_time >=
                        to_date('2015-01-01 00:00:00',
                                'yyyy-mm-dd hh24:mi:ss')
                    and occur_time <=
                        to_date('2015-04-17 00:00:00',
                                'yyyy-mm-dd hh24:mi:ss')
                  order by occur_time) loop
      begin
        newval := oldval + dbms_random.value * 4;
        sqlStr := 'update dd_hs_0002 set cur_14=' || newval || ', cur_16=' ||
                  ((oldval * 0.8 + newval * 0.8) / 2) || ' where occur_time=' ||
                  octime.occur_time;
        oldval := newval;
        --dbms_output.put_line(sqlStr);
        execute immediate sqlStr;
        commit;
      
      exception
        when others then
          rollback work;
    end;
  end loop;