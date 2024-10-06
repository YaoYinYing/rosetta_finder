#!/usr/bin/awk -f

BEGIN{mut_task="";
    mut_info=ARGV[1]
    chain_id=ARGV[2]
    split(mut_info,mut_array,"_");
    for (mut_id in mut_array){
      resid=substr(mut_array[mut_id],2,length(mut_array[mut_id])-2)
      new_mut_task=resid""chain_id
      if(mut_task==""){
        mut_task=new_mut_task
      }
      else {
        mut_task=mut_task","new_mut_task
      }
    }
    print mut_task
}