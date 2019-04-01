#!/usr/bin/perl
# LRH 2015 06 18
# KALD: prog.pl <indfil> 

#Besked ved kald uden parameter.
if ( $#ARGV == -1 )
{
printf("\nDer skal angives en indfil, en bagatelgrænse og en signifikans grænse\n");
printf("\nIndfilen er en liste med jessennumre.\n");
printf("\nBagatelgrænsen bestemmer om et punkt defineres stabit\n"); 
printf("eller ustabilt, signifikansgrænsen er middelfejlen\n"); 
printf("på det enkelte punkt * 3, minimum udsving på den højeste\n");
printf("og max udsving på den laveste, angiver spændet inden for hvilket,\n");
printf("bagatelgrænsen ikke må overskrides.\n");
printf("\nNB! Ved dannelsen af htmlfil peges der på eksakt sted i org-filstruktur\n\n");
printf("\nEks: 5d_ana.pl liste 0.4 3 \n\n");
exit(0);
}


$indfil  = $ARGV[0]; #Liste med jessen numre.
$balimit  = $ARGV[1];#Bagatel grænse.
$silimit  = $ARGV[2];#Signifikans grænse.Hvad middelfejlen på det enkelte punkt ganges med.
#$stlimit  = $ARGV[3];#Stabilitets grænse.

##############################################
#Her laves mapper til de enkelte tidsserier.
###########################################

open(OUT ,">mapper");
open(IN, "$indfil");

while (<IN>) {

$nf =  @li = split;
if ( $nf == 1 )
{
printf( OUT "mkdir %s\n", $li[0]);
}
}

close(IN);
close(OUT);
 
system("mkdir INDFILER"); 
system("mkdir LOGFILER"); 
system("mkdir GISFILER"); 

system("chmod +x mapper");
system("mapper");
system("rm mapper");


###############################
#Så hentes input filer fra res_filer
###############################

open(OUT ,">get");
open(IN, "$indfil");

while (<IN>) {

$nf =  @li = split;
if ( $nf == 1 )
{
printf( OUT "gettimeseries.py %s\n", $li[0]);
}
}

close(IN);
close(OUT);
 
system("chmod +x get");
system("get");
system("rm get");
system("mv *txt INDFILER/.");


################################
#Kørsel af 5d.py.
################################

open(OUT ,">5dfil");
open(IN, "$indfil");

while (<IN>) {

$nf =  @li = split;
if ( $nf == 1 )
{
printf( OUT "5d.py INDFILER/ts_%s.txt INDFILER/ts_%s_xy.txt -o %s -html -map -inc INC/%s_pkt.txt -ilim $balimit -sdi $silimit -log LOGFILER/%s.log\n", $li[0], $li[0], $li[0], $li[0], $li[0]);
}
}

close(IN);
close(OUT);
 
system("chmod +x 5dfil");
system("5dfil");
system("rm 5dfil");


###############################
#urlfil laves
###############################

open(OUT ,">hoved");
open(OUT1 ,">hale");

print(OUT "#DK_idt\n");
print(OUT1 "-1z");

close(OUT);
close(OUT1);

system("rm INDFILER/tmp_id*");
system("cat INDFILER/id* > pip");
system("grep -v DK pip > pip1");
system("grep -v z pip1 > pip2");
system("cat hoved pip2 hale > pip3");
system("doubout -hf -fpip3 -oidfil");
system("fromcrd -fidfil -okote -lDK_h_dvr90 -c3");
system("fromcrd -fkote -okoor -lDK_utm32Leuref89 -c3");
system("grep ' m' koor | cut -c6-17,22-36,43-55 > 1b");
system("grep ' m' kote | cut -c26-32,38-50 > 2b");
system("paste 1b 2b > indfil");

open(OUT ,">urlfil");
open(IN1, "indfil");

print(OUT "Punktnr  N(m)utm32_etrs89  E(m)utm32_etrs89  Kote(m)dvr90  Måleår  URL\n");

while (<IN1>) {

s/\./\,/g;
s/m//g;   
s/  /kk/g;
s/ //g;
s/kk/ /g;
s/G\,/G\./;
s/M\,/M\./;
s/I\,/I\./;
s/V\,/V\./;

$nf =  @li = split;
if ( $nf == 5 )
{
printf( OUT "%s  %s  %s  %s  %s  http://valdemar.kms.dk/cgi-valdemar/valdebsktxt?rgn=DK&stn=%s&crd=geoLeuref89&hgt=h_dvr90\n",
$li[0], $li[1], $li[2], $li[3], $li[4], $li[0]);
}
}

close(IN1);
close(OUT);
 
system("rm 1b 2b indfil kote koor idfil pip*");
system("mv urlfil GISFILER/.");


##########################
#her laves fil med link til html-fil
#########################

system("cat hoved $indfil hale > jessen");
system("fromcrd -fjessen -okote -lDK_h_dvr90");
system("grep -v ' t ' kote > kote1");
system("fromcrd -fkote1 -okoor -lDK_utm32Leuref89 -c3");
system("grep ' m' koor | cut -c6-17,22-36,43-55 > 1b");
system("grep ' m' kote1 | cut -c26-32,38-50 > 2b");
system("paste 1b 2b > indfil");


open(OUT ,">htmlfil");
open(IN1, "indfil");

print(OUT "Punktnr  N(m)utm32_etrs89  E(m)utm32_etrs89  Kote(m)dvr90  Måleår  html\n");


while (<IN1>) {

s/\./\,/g;
s/m//g;   
s/  /kk/g;
s/ //g;
s/kk/ /g;
s/G\,/G\./;
s/M\,/M\./;
s/I\,/I\./;
s/V\,/V\./;

$nf =  @li = split;
if ( $nf == 5 )
{
printf( OUT "%s  %s  %s  %s  %s  F:\\GRF\\DATA\\GEO\\BC\\TID\\5D\\DK1\\%s\\ts_%s.html\n",
$li[0], $li[1], $li[2], $li[3], $li[4], $li[0], $li[0]);
}
}

close(IN1);
close(OUT);
 
system("rm 1b 2b indfil kote kote1 koor jessen");
system("mv htmlfil GISFILER/.");


###################################
#her laves fil med 5dpunkter
###################################

system("net.pl net5d");
system("fromcrd -fnet5d -o5dkms -lDK_utm32Letrs89");
system("gm.pl 5dkms 5dgm");
system("cat hoved 5dgm > 5dgm1");
system("mv 5dgm1 GISFILER/5dpunkter");
system("rm 5dgm 5dkms net5d");
system("rm refgeo.message");
system("rm notfound.crd");


##############################
#Kontrol af om samme fastholdt i ts.
################################

open(OUT , ">kontrol");
open(IN1 , "$indfil");

while (<IN1>) {

$nf =  @li = split;
if ( $nf == 1 )
{
printf( OUT "grep -A 2 'DK_hts_dvr90' //home//ADJ*//ADJ*//*%s_1d > fast_%s
\n",
$li[0], $li[0]);
 
} 
} 

close(IN1);
close(OUT);

system("chmod +x kontrol");
system("kontrol");

system("cat fast* > alle\n");
system("grep -v geo alle > alle1\n");
system("grep ' m ' alle1 | cut -c40-44,68-84> tjekfaste\n");
system("rm kontrol fast_* alle*\n");


######################################
#Antal stabile punkter i punktgruppen.
######################################

system("grep 'Unstable' LOGFILER/* > ustabile");


#############################################################
#Her laves xml fil til GM, hurtig zoom på de enkelte punkter.
#############################################################

system("cat hoved $indfil hale > indfil");
system("fromcrd -findfil -ogeo -lDK_geoLetrs89");
system("kmstr5 <geo >geo1 -#DK_geoLetrs89 -d2 -tdg -r -s -u");
system("grep ' 81 ' geo1 > geo2");

open(OUT ,">locations.xml");
open(IN ,"geo2");

print(OUT "<?xml version='1.0' encoding='UTF-8'?>\n");
print(OUT "-<NamedLocationConfiguration xmlns='http://www.intergraph.com/GeoMedia' fileVersion='2.0'>\n");

while (<IN>) {

s/81 /81/;

$nf =  @li = split;
if ( $nf >= 1)

{
printf( OUT "<Location xmlns='' IsGlobal='True' Rotation='0' Tilt='-90' Roll='0' DisplayScale='8000' CenterZ='0' CenterY='%s' CenterX='%s' Name='%s'/>\n",
$li[1], $li[2], $li[0]);
}
}

print(OUT "</NamedLocationConfiguration>\n");

close(IN);
close(OUT);
 
system("mv locations.xml GISFILER/.");
system("rm indfil geo geo1 geo2 hoved hale transrep refgeo* notfound*");
