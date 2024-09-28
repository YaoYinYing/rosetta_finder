#!/usr/bin/awk -f

BEGIN{
    mut_info=ARGV[1]
    chain_id=ARGV[2]
    mut_protocol="";
    split(mut_info,mut_array,"_");
    for (mut_id in mut_array){
      new_mut_protocol="<Add mover_name=\"mr"mut_id"\"/>"
      if(mut_protocol==""){
        mut_protocol=new_mut_protocol
      }
      else {
        mut_protocol=mut_protocol""new_mut_protocol
      }
      }
    print mut_protocol
    }