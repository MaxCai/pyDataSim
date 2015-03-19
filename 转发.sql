--update yc_send_x
declare
	v_no number(10);
	sql_str varchar2(300);
	v_table_name varchar2(20);
	cursor get_table_no is
	select trans_table_no from temp_Trans_Config group by trans_table_no;

begin
		for c1_rec in get_table_no
		loop
		begin
			v_table_name := 'yc_send_'||c1_rec.trans_table_no;
			sql_str := 'update '|| v_table_name ||' t1  set (t1.ld_id,send_no) = (select distinct ld_id,order_no  from (select * from id_no_trans where id_no_trans.trans_table_no= '||c1_rec.trans_table_no||' ) t2 where t1.yc_id=t2.id) 
			where exists(select 1 from (select * from id_no_trans where id_no_trans.trans_table_no= '||c1_rec.trans_table_no||' ) t2  where t1.yc_id=t2.id)';
			dbms_output.put_line(sql_str);
			execute immediate sql_str;
			commit;
			EXCEPTION
            when others then
            ROLLBACK WORK;
		end;
		end loop;
end;