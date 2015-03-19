DECLARE
 ct number(10);
 bayreg varchar2(100);
 sql_str varchar2(200);
BEGIN
    FOR bay in (select bay_alias from bay_info where bay_alias like 'WF01.Sub.%' or bay_alias like 'WF02.Sub.%') LOOP
        BEGIN
        ct := 2;
        bayreg := bay.bay_alias || '%';
        FOR ai IN (select yc_id from yc_define where yc_alias like bayreg) LOOP
        BEGIN
            sql_str := 'update yc_channel set order_no = '|| ct || 'where yc_id = ' || ai.yc_id;
            dbms_output.put_line(sql_str);
            execute immediate sql_str;
            commit;
            ct := ct+1;
            EXCEPTION
            when others then
            ROLLBACK WORK;
        END;
        END LOOP;
        END;
    END LOOP;
            
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
END;
/