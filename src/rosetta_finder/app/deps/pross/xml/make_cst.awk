#! awk -f

{
if (($1=="ATOM" || $1=="HETATM") && $3=="CA"){
    root_aa = substr($0, 23, 4)
    root_aa_chain = substr($0, 22, 1)
    x = substr($0, 31, 8)
    y = substr($0, 39, 8)
    z = substr($0, 47, 8)
    atom = $3
    res_num = substr($0, 23, 4)
    chain = substr($0, 22, 1)
    printf "CoordinateConstraint %s %s%s CA %s%s %s %s %s HARMONIC 0 1\n",atom,res_num,chain,root_aa,root_aa_chain,x,y,z;
};
}