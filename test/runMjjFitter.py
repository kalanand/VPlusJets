#! /usr/bin/env python

from optparse import OptionParser

parser = OptionParser()
parser.add_option('-b', action='store_true', dest='noX', default=False,
                  help='no X11 windows')
parser.add_option('-j', '--Njets', dest='Nj', default=2, type='int',
                  help='Number of jets.')
parser.add_option('--fSU', dest='e_FSU', default=-100.0, type='float',
                  help='Externally set scaling up fraction. It is the scaling down fraction when -1.0<fSU<0.0; and it is taken from the input file when fSU<-10.0.')
parser.add_option('--fMU', dest='e_FMU', default=-100.0, type='float',
                  help='Externally set matching up fraction. It is the matching down fraction when -1.0<fMU<0.0; and it is taken from the input file when fMU<-10.0.')
parser.add_option('--TD', dest='toydataFile', default='',
                  help='a file corresponding to a toy dataset')
parser.add_option('-i', '--init', dest='startingFile',
                  default='MjjNominal2Jets.txt',
                  help='File to use as the initial template')
parser.add_option('-d', '--dir', dest='mcdir', default='',
                  help='directory to pick up the W+jets shapes')
parser.add_option('-m', '--mode', default="MjjOptimizeConfig",
                  dest='modeConfig',
                  help='which config to select look at HWWconfig.py for an '+ \
                  'example.  Use the file name minus the .py extension.')
parser.add_option('-q', action='store_true', dest='qplot', default=False,
                  help='make Q plot also.')
parser.add_option('--NP', action='store_true', dest='NP', default=False,
                  help='put NP on the plot')
parser.add_option('--Err', dest='Err', default=-1., type='float',
                  help='error band level')
(opts, args) = parser.parse_args()

import pyroot_logon
config = __import__(opts.modeConfig)

from ROOT import gPad, TFile, Double, Long, gROOT, TCanvas
## gROOT.ProcessLine('.L RooWjjFitterParams.h+');
gROOT.ProcessLine('.L EffTableReader.cc+')
gROOT.ProcessLine('.L EffTableLoader.cc+')
gROOT.ProcessLine('.L RooWjjFitterUtils.cc+')
gROOT.ProcessLine('.L RooWjjMjjFitter.cc+')
from ROOT import RooWjjMjjFitter, RooFitResult, \
     RooMsgService, RooFit, TLatex, TMatrixDSym, RooArgList, RooArgSet, \
     gPad, RooAbsReal, kBlue, kCyan, kRed
from math import sqrt


RooMsgService.instance().setGlobalKillBelow(RooFit.WARNING)

fitterPars = config.theConfig(opts.Nj, opts.mcdir, opts.startingFile, opts.toydataFile )
if fitterPars.includeMuons and fitterPars.includeElectrons:
    modeString = ''
elif fitterPars.includeMuons:
    modeString = 'Muon'
elif fitterPars.includeElectrons:
    modeString = 'Electron'
else:
    modeString = ''

theFitter = RooWjjMjjFitter(fitterPars)

theFitter.makeFitter(False)

#theFitter.getWorkSpace().Print()
fr = theFitter.fit()

chi2 = Double(0.)
#ndf = Long(2)
extraNdf = 0
if (fitterPars.doNewPhysics):
    extraNdf += 1
if not fitterPars.constrainDiboson:
    extraNdf += 1
ndf = Long(3+extraNdf)
theFitter.computeChi2(chi2, ndf)
# chi2frame.Draw()

# assert False, "fit done"

yields = fr.floatParsFinal()
mass = theFitter.getWorkSpace().var(fitterPars.var)
iset = RooArgSet(mass)
covMatrix = TMatrixDSym(fr.covarianceMatrix())

sig2 = 0.
for v1 in range(0, covMatrix.GetNrows()):
    for v2 in range(0, covMatrix.GetNcols()):
        if ((yields[v1].GetName())[0] == 'n') and \
               ((yields[v2].GetName())[0] == 'n'):
            sig2 += covMatrix(v1, v2)

mf = theFitter.stackedPlot()
sf = theFitter.residualPlot(mf, "h_background", "dibosonPdf", False)
pf = theFitter.residualPlot(mf, "h_total", "", True)
lf = theFitter.stackedPlot(True)


if opts.Err > 0:
    totalPdf = theFitter.getWorkSpace().pdf('totalPdf')
    ## Ntotal = totalPdf.expectedEvents(iset)

    ## print 'Ntotal:',Ntotal

    totalPdf.plotOn(sf,
                    RooFit.ProjWData(theFitter.getWorkSpace().data('data')),
                    RooFit.Normalization(opts.Err, RooAbsReal.Raw),
                    RooFit.AddTo('h_dibosonPdf', 1., 1.),
                    RooFit.Name('h_ErrUp'),
                    RooFit.LineColor(kRed), RooFit.LineStyle(3))
    totalPdf.plotOn(sf,
                    RooFit.ProjWData(theFitter.getWorkSpace().data('data')),
                    RooFit.Normalization(opts.Err, RooAbsReal.Raw),
                    RooFit.AddTo('h_dibosonPdf', -1., 1.),
                    RooFit.Name('h_ErrDown'),
                    RooFit.LineColor(kRed), RooFit.LineStyle(3))
    sf.drawBefore('h_ErrUp', 'h_dibosonPdf')
    sf.drawBefore('h_ErrDown', 'h_dibosonPdf')
    h_ErrUp = sf.getCurve('h_ErrUp')
    sf.findObject('theLegend').AddEntry(h_ErrUp, 'Uncertainty', 'L')

if opts.NP:
    NPPdf = theFitter.makeNPPdf();
    NPNorm = 4.*0.11*46.8/12.*fitterPars.intLumi

    if (modeString == 'Electron'):
        if opts.Nj == 2:
            NPNorm *= 0.037
        elif opts.Nj == 3:
            NPNorm *= 0.012
    else:
        if opts.Nj == 2:
            NPNorm *= 0.051
        elif opts.Nj == 3:
            NPNomr *= 0.016

    print '**** N_NP:', NPNorm,'****'

    NPPdf.plotOn(sf, RooFit.ProjWData(theFitter.getWorkSpace().data('data')),
                 RooFit.Normalization(NPNorm, RooAbsReal.Raw),
                 RooFit.Name('h_NP'),
                 RooFit.LineColor(kCyan+2), RooFit.LineStyle(2))

    h_NP = sf.getCurve('h_NP')

    sf.drawBefore('h_NP', 'theData')

    sf.findObject('theLegend').AddEntry(h_NP, "CDF-like Gaussian", "L")

l = TLatex()
l.SetNDC()
l.SetTextSize(0.035)
l.SetTextFont(42)

cstacked = TCanvas("cstacked", "stacked")
mf.Draw()
l.DrawLatex(0.55, 0.55,
            '#chi^{{2}}/dof = {0:0.3f}/{1} = {2:0.3f}'.format(chi2, ndf,
                                                              chi2/ndf)
            )
pyroot_logon.cmsPrelim(cstacked, fitterPars.intLumi/1000)
cstacked.Print('Wjj_Mjj_{0}_{1}jets_Stacked.pdf'.format(modeString, opts.Nj))
cstacked.Print('Wjj_Mjj_{0}_{1}jets_Stacked.png'.format(modeString, opts.Nj))
c2 = TCanvas("c2", "stacked_log")
c2.SetLogy()
lf.Draw()
pyroot_logon.cmsPrelim(c2, fitterPars.intLumi/1000)
c2.Print('Wjj_Mjj_{0}_{1}jets_Stacked_log.pdf'.format(modeString, opts.Nj))
c2.Print('Wjj_Mjj_{0}_{1}jets_Stacked_log.png'.format(modeString, opts.Nj))
c3 = TCanvas("c3", "subtracted")
sf.Draw()
pyroot_logon.cmsPrelim(c3, fitterPars.intLumi/1000)
c3.Print('Wjj_Mjj_{0}_{1}jets_Subtracted.pdf'.format(modeString,opts.Nj))
c3.Print('Wjj_Mjj_{0}_{1}jets_Subtracted.png'.format(modeString,opts.Nj))
c4 = TCanvas("c4", "pull")
pf.Draw()
pyroot_logon.cmsPrelim(c4, fitterPars.intLumi/1000)
c4.Print('Wjj_Mjj_{0}_{1}jets_Pull.pdf'.format(modeString, opts.Nj))
c4.Print('Wjj_Mjj_{0}_{1}jets_Pull.png'.format(modeString, opts.Nj))

h_total = mf.getCurve('h_total')
theData = mf.getHist('theData')

mass.setRange('signal', fitterPars.minTrunc, fitterPars.maxTrunc)
sigInt = theFitter.makeFitter().createIntegral(iset, 'signal')
sigFullInt = theFitter.makeFitter().createIntegral(iset)
dibosonInt = theFitter.makeDibosonPdf().createIntegral(iset, 'signal')
dibosonFullInt = theFitter.makeDibosonPdf().createIntegral(iset)
WpJInt = theFitter.makeWpJPdf().createIntegral(iset, 'signal')
WpJFullInt = theFitter.makeWpJPdf().createIntegral(iset)
ttbarInt = theFitter.makettbarPdf().createIntegral(iset, 'signal')
ttbarFullInt = theFitter.makettbarPdf().createIntegral(iset)
SingleTopInt = theFitter.makeSingleTopPdf().createIntegral(iset, 'signal')
SingleTopFullInt = theFitter.makeSingleTopPdf().createIntegral(iset)
QCDInt = theFitter.makeQCDPdf().createIntegral(iset, 'signal')
QCDFullInt = theFitter.makeQCDPdf().createIntegral(iset)
ZpJInt = theFitter.makeZpJPdf().createIntegral(iset, 'signal')
ZpJFullInt = theFitter.makeZpJPdf().createIntegral(iset)
## print "*** yield vars ***"
## yields.Print("v")

usig2 = 0.
totalYield = 0.

sigYieldsFile = open('lastMjjSigYield.txt', 'w')
print
print '-------------------------------'
print 'Yields in signal box'
print '-------------------------------'
for i in range(0, yields.getSize()):
    theName = yields.at(i).GetName()
    if theName[0] == 'n':
        totalYield += yields.at(i).getVal()
        theIntegral = 1.
        if (theName == 'nDiboson'):
            theIntegral = dibosonInt.getVal()/dibosonFullInt.getVal()
        elif (theName == 'nWjets'):
            theIntegral = WpJInt.getVal()/WpJFullInt.getVal()
        elif (theName == 'nTTbar'):
            theIntegral = ttbarInt.getVal()/ttbarFullInt.getVal()
        elif (theName == 'nSingleTop'):
            theIntegral = SingleTopInt.getVal()/SingleTopFullInt.getVal()
        elif (theName == 'nQCD'):
            theIntegral = QCDInt.getVal()/QCDFullInt.getVal()
        elif (theName == 'nZjets'):
            theIntegral = ZpJInt.getVal()/ZpJFullInt.getVal()

        yieldString = '{0} = {1:0.0f} +/- {2:0.0f}'.format(theName,
                                                  yields.at(i).getVal()*theIntegral,
                                                  yields.at(i).getError()*theIntegral)
        print yieldString
    else:
        yieldString = '{0} = {1:0.3f} +/- {2:0.3f}'.format(theName,
                                                           yields.at(i).getVal(),
                                                           yields.at(i).getError())
    sigYieldsFile.write(yieldString + '\n')
print '-------------------------------'
print 'total yield: {0:0.0f} +/- {1:0.0f}'.format(totalYield*sigInt.getVal()/sigFullInt.getVal(), sigInt.getVal()*sqrt(sig2))
print '-------------------------------'

sigYieldsFile.close()

if opts.qplot:
    import makeQPlot
    qplotPars = makeQPlot.theConfig(fitterPars, 'lastMjjSigYield.txt')
    (cq, shapeHist, totalHist) = makeQPlot.qPlot(qplotPars)
    pyroot_logon.cmsPrelim(cq, fitterPars.intLumi/1000)
    cq.Print('Wjj_Mjj_{0}_{1}jets_Q.pdf'.format(modeString, opts.Nj))
    cq.Print('Wjj_Mjj_{0}_{1}jets_Q.png'.format(modeString, opts.Nj))

fr.Print()
nll=fr.minNll()
print '***** nll = ',nll,' ***** \n'
print 'total yield: {0:0.0f} +/- {1:0.0f}'.format(totalYield, sqrt(sig2))

print 'shape file created'
ShapeFile = TFile('Mjj_{1}_{0}Jets_Fit_Shapes.root'.format(opts.Nj,
                                                           modeString),
                  'recreate')
h_total.Write()
theData.Write()
ShapeFile.Close()
