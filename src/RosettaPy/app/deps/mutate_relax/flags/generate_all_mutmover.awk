#!/usr/bin/awk -f
BEGIN{
    res_map["C"] = "CYS"
    res_map["H"] = "HIS"
    res_map["D"] = "ASP"
    res_map["E"] = "GLU"
    res_map["K"] = "LYS"
    res_map["S"] = "SER"
    res_map["R"] = "ARG"
    res_map["T"] = "THR"
    res_map["N"] = "ASN"
    res_map["Q"] = "GLN"
    res_map["Y"] = "TYR"
    res_map["M"] = "MET"
    res_map["G"] = "GLY"
    res_map["W"] = "TRP"
    res_map["P"] = "PRO"
    res_map["A"] = "ALA"
    res_map["V"] = "VAL"
    res_map["I"] = "ILE"
    res_map["L"] = "LEU"
    res_map["F"] = "PHE"

    mut_info=ARGV[1]
    chain_id=ARGV[2]
    mut_mover="";
    split(mut_info,mut_array,"_");
    for (mut_id in mut_array){
      resid=substr(mut_array[mut_id],2,length(mut_array[mut_id])-2)
      res_mut=substr(mut_array[mut_id],length(mut_array[mut_id]),1)
      new_mut_mover="<MutateResidue name=\"mr"mut_id"\" target=\""resid""chain_id"\" new_res=\""res_map[res_mut]"\"/>"
      if(mut_mover==""){
        mut_mover=new_mut_mover
      }
      else {
        mut_mover=mut_mover""new_mut_mover
      }
      }
    print mut_mover
    }