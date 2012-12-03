from RooWjj2DFitterUtils import Wjj2DFitterUtils
from ROOT import RooWorkspace, RooAddPdf, RooAbsReal, RooFit, RooCmdArg, \
    RooBinning, RooAbsData, RooHist, RooArgList, RooArgSet, TFile, RooDataHist,\
    kRed, kBlue, kGreen, kYellow, kGray, kAzure, kCyan, gROOT, TLegend
from math import sqrt
from array import array
import sys

colorwheel = [ kAzure+8,
               kRed,
               kGreen+2,
               kGray+1,
               kYellow,
               kCyan+2
               ]
class Wjj2DFitter:

    def __init__ (self, pars):
        self.pars = pars
        self.ws = RooWorkspace('wjj2dfitter')
        self.utils = Wjj2DFitterUtils(self.pars)

        for v in self.pars.var:

            var1 = self.ws.factory('%s[%f,%f]' % (v, 
                                                  self.pars.varRanges[v][1], 
                                                  self.pars.varRanges[v][2])
                                   )
            var1.setUnit('GeV')
            try:
                var1.SetTitle(self.pars.varTitles[v])
            except AttributeError:
                var1.SetTitle('m_{jj}')
            var1.setPlotLabel(var1.GetTitle())
            if len(self.pars.varRanges[v][3]) > 1:
                vbinning = RooBinning(len(self.pars.varRanges[v][3]) - 1, 
                                   array('d', self.pars.varRanges[v][3]),
                                   '%sBinning' % v)
                var1.setBinning(vbinning)
            else:
                var1.setBins(self.pars.varRanges[v][0])
            var1.Print()
        self.ws.defineSet('obsSet', ','.join(self.pars.var))

    def loadWorkspaceFromFile(self, filename, wsname = 'w'):
        print 'loading data workspace %s from file %s' % (wsname, filename)
        fin = TFile.Open(filename)
        other = fin.Get(wsname)

        #pull unbinned data from other workspace
        unbinnedData = other.data('data_unbinned')
        if not unbinnedData:
            unbinnedData = other.data('data_obs')

        if self.pars.binData:
            #bin and import data
            unbinnedData.SetName('data_unbinned')
            getattr(self.ws, 'import')(unbinnedData)
            data = RooDataHist('data_obs', 'data_obs', other.set('obsSet'), 
                               unbinnedData)
            getattr(self.ws, 'import')(data)
        else:
            #just import data
            unbinnedData.SetName('data_obs')
            getattr(self.ws, 'import')(unbinnedData)

        self.ws.Print()
    
    # put together a fitting model and return the pdf
    def makeFitter(self):
        if self.ws.pdf('total'):
            return self.ws.pdf('total')

        compPdfs = []
        for component in self.pars.backgrounds:
            compFiles = getattr(self.pars, '%sFiles' % component)
            compModels = getattr(self.pars, '%sModels' % component)
            compPdf = self.makeComponentPdf(component, compFiles, 
                                            compModels)
                
            norm = self.ws.factory('prod::f_%s_norm' % component + \
                                       '(n_%s[0.,1e6],' % component + \
                                       '%s_norm[1.,-0.5,5.])' % component)
            self.ws.var('n_%s' % component).setConstant(True)
            compPdfs.append(
                self.ws.factory('RooExtendPdf::%s_extended(%s,%s)' % \
                                    (compPdf.GetName(), 
                                     compPdf.GetName(),
                                     norm.GetName())
                                )
                )
                                    
            
        for component in self.pars.signals:
            compFile = getattr(self.pars, '%sFiles' % component)
            compModels = getattr(self.pars, '%sModels' % component)
            compPdf = self.makeComponentPdf(component, compFiles,
                                            compModels)
            norm = self.ws.factory(
                "prod::f_%s_norm(n_%s[0., 1e6],r_%s[0.,-20.,20.])" % \
                    (component, component, component)
                )
            self.ws.var('n_%s' % component).setConstant(True)
            self.ws.var('r_%s' % component).setConstant(False)
            pdf = self.ws.factory('RooExtendPdf::%s_extended(%s,%s)' % \
                                      (compPdf.GetName(), 
                                       compPdf.GetName(),
                                       norm.GetName())
                                  )
            
            if self.pars.includeSignal:
                compPdfs.append(pdf)

        #print compPdfs
        
        prodList = [ '%s' % (pdf.GetName()) \
                         for (idx, pdf) in enumerate(compPdfs) ]
        comps = RooArgList(self.ws.argSet(','.join(prodList)))
        getattr(self.ws, 'import')(RooAddPdf('total', 'total', comps))

        return self.ws.pdf('total')

    # define the constraints on the yields, etc that will be part of the fit.
    def makeConstraints(self):

        if self.ws.set('constraintSet'):
            return self.ws.set('constraintSet')

        constraints = []
        constrainedParameters = []
        for constraint in self.pars.yieldConstraints:
            theYield = self.ws.var('%s_norm' % constraint)
            if not theYield.isConstant():
                self.ws.factory('RooGaussian::%s_const(%s, 1.0, %f)' % \
                                    (constraint, theYield.GetName(),
                                     self.pars.yieldConstraints[constraint])
                                )
                constraints.append('%s_const' % constraint)
                constrainedParameters.append(theYield.GetName())

        if hasattr(self.pars, 'constrainShapes'):
            for component in self.pars.constrainShapes:
                pc = self.ws.pdf(component).getParameters(self.ws.set('obsSet'))
                parIter = pc.createIterator()
                par = parIter.Next()
                while par:
                    if not par.isConstant():
                        theConst = self.ws.factory('RooGaussian::%s_const' % \
                                                       (par.GetName()) + \
                                                       '(%s, %f, %f)' % \
                                                       (par.GetName(),
                                                        par.getVal(),
                                                        par.getError())
                                                   )
                        constraints.append(theConst.GetName())
                        constrainedParameters.append(par.GetName())
                    par = parIter.Next()
                pc.IsA().Destructor(pc)

        self.ws.defineSet('constraintSet', ','.join(constraints))
        self.ws.defineSet('constrainedSet', ','.join(constrainedParameters))

        return self.ws.set('constraintSet')

    # set the yield of the multijet background
    def setMultijetYield(self):
        if self.ws.var('n_multijet'):
            self.multijetExpected = self.ws.data('data_obs').sumEntries() * \
                self.pars.multijetFraction
            self.ws.var('n_multijet').setVal(self.multijetExpected)

    # fit the data using the pdf
    def fit(self):
        print 'construct fit pdf ...'
        fitter = self.makeFitter()

        print 'load data ...'
        data = self.loadData()

        self.setMultijetYield()

        self.resetYields()

        constraintSet = self.makeConstraints()

        self.readParametersFromFile()

        # print constraints, self.pars.yieldConstraints
        print '\nfit constraints'
        constIter = constraintSet.createIterator()
        constraint = constIter.Next()
        constraints = []
        while constraint:
            constraint.Print()
            constraints.append(constraint.GetName())
            constraint = constIter.Next()
            
        constraintCmd = RooCmdArg.none()
        if constraintSet.getSize() > 0:
            constraints.append(fitter.GetName())
            fitter = self.ws.factory('PROD::totalFit_const(%s)' % \
                                         (','.join(constraints))
                                     )
            constraintCmd = RooFit.Constrained()
            # constraintCmd = RooFit.ExternalConstraints(self.ws.set('constraintSet'))

        self.ws.Print()

        # for constraint in pars.constraints:
        #     self.ws.pdf(constraint).Print()
        # print

        print 'fitting ...'
        fr = fitter.fitTo(data, RooFit.Save(True),
                          RooFit.Extended(True),
                          RooFit.Minos(False),
                          RooFit.PrintEvalErrors(-1),
                          RooFit.Warnings(False),
                          constraintCmd)
        fr.Print()

        return fr

    # determine the fitting model for each component and return them
    def makeComponentPdf(self, component, files, models):
        if (models[0] == -1):
            thePdf = self.makeComponentHistPdf(component, files)
        elif (models[0] == -2):
            return self.makeComponentMorphingPdf(component, files)
        else:
            thePdf = self.makeComponentAnalyticPdf(component, models)
        return thePdf
            
    #create a simple 2D histogram pdf
    def makeComponentHistPdf(self, component, files):
        if self.ws.pdf(component):
            return self.ws.pdf(component)

        compHist = self.utils.newEmptyHist('hist%s' % component)
        sumYields = 0.
        sumxsec = 0.
        sumExpected = 0.
        for (idx,fset) in enumerate(files):
            filename = fset[0]

            tmpHist = self.utils.File2Hist(filename, 
                                           'hist%s_%i' % (component, idx))
            sumYields += tmpHist.Integral()
            sumxsec += fset[2]
            compHist.Add(tmpHist, self.pars.integratedLumi*fset[2]/fset[1])
            sumExpected += tmpHist.Integral()*fset[2]* \
                self.pars.integratedLumi/fset[1]
            print filename,'acc x eff: %.3g' % (tmpHist.Integral()/fset[1])
            print filename,'N_expected: %.1f' % \
                (tmpHist.Integral()*fset[2]*self.pars.integratedLumi/fset[1])
            #tmpHist.Print()

        #compHist.Print()
        print '%s acc x eff: %.3g' % \
            (component, sumExpected/sumxsec/self.pars.integratedLumi)
        print 'Number of expected %s events: %.1f' % (component, sumExpected)
        setattr(self, '%sExpected' % component, sumExpected)

        return self.utils.Hist2Pdf(compHist, component, 
                                   self.ws, self.pars.order)

    # create a pdf using the "template morphing" technique
    def makeComponentMorphingPdf(self, component, files):
        # TODO: implement template morphing if needed.
        return []

    # create a pdf using an analytic function.
    def makeComponentAnalyticPdf(self, component, models):
        if self.ws.pdf(component):
            return self.ws.pdf(component)

        pdfList = []
        for (idx,model) in enumerate(models):
            var = self.pars.var[idx]
            pdfList.append(self.utils.analyticPdf(self.ws, var, model, 
                                                  '%s_%s' % \
                                                      (component,var), 
                                                  '%s_%s'%(component,var)
                                                  )
                           )
        
        pdfList = [ pdf.GetName() for pdf in pdfList ]
        if len(pdfList) > 1:
            self.ws.factory('PROD::%s(%s)' % (component, ','.join(pdfList)))
        else:
            pdfList[0].SetName(component)
                        
        return self.ws.pdf(component)

    def loadData(self, weight = False):
        if self.ws.data('data_obs'):
            return self.ws.data('data_obs')

        unbinnedName = 'data_obs'
        if self.pars.binData:
            unbinnedName = 'data_unbinned'
        data = self.utils.File2Dataset(self.pars.DataFile, unbinnedName, 
                                       self.ws, weighted = weight)
        if self.pars.binData:
            data = RooDataHist('data_obs', 'data_obs', self.ws.set('obsSet'), 
                               data)
            getattr(self.ws, 'import')(data)
            data = self.ws.data('data_obs')

        return data

    def stackedPlot(self, var, logy = False, pdfName = None):
        if not pdfName:
            pdfName = 'total'

        xvar = self.ws.var(var)

        sframe = xvar.frame()
        sframe.SetName("%s_stacked" % var)
        pdf = self.ws.pdf(pdfName)

        if isinstance(pdf, RooAddPdf):
            compList = RooArgList(pdf.pdfList())
        else:
            compList = None

        data = self.ws.data('data_obs')
        nexp = pdf.expectedEvents(self.ws.set('obsSet'))

        print pdf.GetName(),'expected: %.0f' % (nexp)
        print 'data events: %.0f' % (data.sumEntries())

        if nexp < 1:
            nexpt = data.sumEntries()
        theComponents = self.pars.backgrounds
        if self.pars.includeSignal:
            theComponents += self.pars.signals
        # data.plotOn(sframe, RooFit.Invisible(),
        #             RooFit.Binning('%sBinning' % (var)))
        dataHist = RooAbsData.createHistogram(data,'dataHist_%s' % var, xvar,
                                              RooFit.Binning('%sBinning' % var))
        #dataHist.Scale(1., 'width')
        invData = RooHist(dataHist, 1., 1, RooAbsData.SumW2, 1.0, True)
        #invData.Print('v')
        sframe.addPlotable(invData, 'pe', True, True)
        for (idx,component) in enumerate(theComponents):
            print '\nplotting',component,'...'
            if hasattr(self.pars, '%sPlotting' % (component)):
                plotCharacteristics = getattr(self.pars, '%sPlotting' % \
                                                  (component))
            else:
                plotCharacteristics = {'color' : colorwheel[idx%6],
                                       'title' : component }

            compCmd = RooCmdArg.none()
            if compList:
                compSet = RooArgSet(compList)
                compCmd = RooFit.Components(compSet)
                removals = compList.selectByName('%s*' % component)
                compList.remove(removals)

            sys.stdout.flush()
            pdf.plotOn(sframe, RooFit.ProjWData(data),
                       RooFit.DrawOption('LF'), RooFit.FillStyle(1001),
                       RooFit.FillColor(plotCharacteristics['color']),
                       RooFit.LineColor(plotCharacteristics['color']),
                       RooFit.VLines(),
                       #RooFit.Normalization(nexp, RooAbsReal.Raw),
                       compCmd
                       )
            tmpCurve = sframe.getCurve()
            tmpCurve.SetName(component)
            tmpCurve.SetTitle(plotCharacteristics['title'])

        theData = RooHist(dataHist, 1., 1, RooAbsData.SumW2, 1.0, True)
        theData.SetName('theData')
        theData.SetTitle('data')
        sframe.addPlotable(theData, 'pe')

        if (logy):
            sframe.SetMinimum(0.01)
            sframe.SetMaximum(1.0e6)

        sframe.GetYaxis().SetTitle('Events / GeV')

        return sframe

    def readParametersFromFile(self, fname=None):
        if (not fname):
            fname = self.pars.initialParametersFile
        
        if isinstance(fname, str):
            flist = [ fname ]
        else:
            flist = fname

        for tmpName in flist:
            if len(tmpName) > 0:
                print 'loading parameters from file',tmpName
                self.ws.allVars().readFromFile(tmpName)

    def expectedFromPars(self):
        components = self.pars.signals + self.pars.backgrounds
        for component in components:
            theYield = self.ws.var('n_%s' % component)
            setattr(self, '%sExpected' % component, theYield.getVal())

    def resetYields(self):
        if self.ws.data('data_obs'):
            Ndata = self.ws.data('data_obs').sumEntries()
        else:
            Ndata = 10000.
        print 'resetting yields...'
        components = self.pars.signals + self.pars.backgrounds
        for component in components:
            theYield = self.ws.var('n_%s' % component)
            theNorm = self.ws.var('%s_norm' % component)
            if hasattr(self, '%sExpected' % component):
                theYield.setVal(getattr(self, '%sExpected' % component))
            else:
                print 'no expected value for',component
                theYield.setVal(Ndata/len(components))
            if theNorm:
                theNorm.setVal(1.0)
            if component in self.pars.yieldConstraints:
                theYield.setError(theYield.getVal() * \
                                      self.pars.yieldConstraints[component])
                if theNorm:
                    theNorm.setError(self.pars.yieldConstraints[component])
            else:
                theYield.setError(sqrt(theYield.getVal()))
            theYield.Print()

    def legend4Plot(plot, left = False):
        if left:
            theLeg = TLegend(0.2, 0.62, 0.55, 0.92, "", "NDC")
        else:
            theLeg = TLegend(0.55, 0.62, 0.92, 0.92, "", "NDC")
        theLeg.SetName('theLegend')

        theLeg.SetBorderSize(0)
        theLeg.SetLineColor(0)
        theLeg.SetFillColor(0)
        theLeg.SetFillStyle(0)
        theLeg.SetLineWidth(0)
        theLeg.SetLineStyle(0)
        theLeg.SetTextFont(42)
        theLeg.SetTextSize(.045)

        entryCnt = 0
        for obj in range(0, int(plot.numItems())):
            objName = plot.nameOf(obj)
            if (not plot.getInvisible(objName)):
                theObj = plot.getObject(obj)
                objTitle = theObj.GetTitle()
                if len(objTitle) < 1:
                    objTitle = objName
                dopts = plot.getDrawOptions(objName).Data()
                # print 'obj:',theObj,'title:',objTitle,'opts:',dopts,'type:',type(dopts)
                theLeg.AddEntry(theObj, objTitle, dopts)
                entryCnt += 1
        theLeg.SetY1NDC(0.9 - 0.05*entryCnt - 0.005)
        theLeg.SetY1(theLeg.GetY1NDC())
        return theLeg

    legend4Plot = staticmethod(legend4Plot)


if __name__ == '__main__':
    import RooWjj2DFitterPars

    pars = RooWjj2DFitterPars.Wjj2DFitterPars()
    pars.backgrounds = ['WpJ']
    pars.signals = []
    pars.WpJFiles = [('', 0, 0)]
    pars.WpJModels = [20, 0]
    
    fitter = Wjj2DFitter(pars)
    fitter.makeFitter()
    fitter.loadData()
    fitter.resetYields()

    fitter.ws.var('turnOn_WpJ_Mass2j_PFCor_0').setVal(60.)
    fitter.ws.var('turnOn_WpJ_Mass2j_PFCor_0').setError(10.)
    fitter.ws.var('width_WpJ_Mass2j_PFCor_0').setVal(20.)
    fitter.ws.var('width_WpJ_Mass2j_PFCor_0').setError(2.)
    fitter.ws.var('c_WpJ_Mass2j_PFCor_1').setVal(-0.015)
    fitter.ws.var('c_WpJ_Mass2j_PFCor_1').setError(0.01)
    fitter.ws.var('c_WpJ_fit_mlvjj').setVal(-0.015)
    fitter.ws.var('c_WpJ_fit_mlvjj').setError(0.01)

    #fitter.fit()
    plot1 = fitter.stackedPlot(pars.var[0])
    plot2 = fitter.stackedPlot(pars.var[1])

    plot1.Draw()

    fitter.ws.Print()
