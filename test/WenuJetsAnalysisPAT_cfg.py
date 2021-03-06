import FWCore.ParameterSet.Config as cms
import pprint
isMC = False

process = cms.Process("demo")

##---------  Load standard Reco modules ------------
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.MagneticField_38T_cff')



##----- this config frament brings you the generator information ----
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("PhysicsTools.HepMCCandAlgos.genParticles_cfi")
process.load("Configuration.StandardSequences.Generator_cff")


##----- Detector geometry : some of these needed for b-tag -------
process.load("TrackingTools.TransientTrack.TransientTrackBuilder_cfi")
##process.load("Configuration.StandardSequences.Geometry_cff")
process.load("Configuration.Geometry.GeometryIdeal_cff")

process.load("Geometry.CMSCommonData.cmsIdealGeometryXML_cfi")
process.load("Geometry.CommonDetUnit.globalTrackingGeometry_cfi")
process.load("RecoMuon.DetLayers.muonDetLayerGeometry_cfi")


##----- B-tags --------------
process.load("RecoBTag.Configuration.RecoBTag_cff")

#//.....QGL:....
process.load('QuarkGluonTagger.EightTeV.QGTagger_RecoJets_cff')


##----- Global tag: conditions database ------------
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

##----- Counter module ------------
process.load("ElectroWeakAnalysis.VPlusJets.AllPassFilter_cfi")

## import skeleton process
#from PhysicsTools.PatAlgos.patTemplate_cfg import *


############################################
if not isMC:
    process.GlobalTag.globaltag = 'GR_R_53_V10::All'
else:
    process.GlobalTag.globaltag = 'START53_V7E::All'

OutputFileName = "WenuJetAnalysisntuple.root"
numEventsToRun = 100
############################################
########################################################################################
########################################################################################

##---------  W-->enu Collection ------------
process.load("ElectroWeakAnalysis.VPlusJets.WenuCollectionsPAT_cfi")

##---------  Jet Collection ----------------
process.load("ElectroWeakAnalysis.VPlusJets.JetCollectionsPAT_cfi")

##---------  Vertex and track Collections -----------
process.load("ElectroWeakAnalysis.VPlusJets.TrackCollections_cfi")
#

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(numEventsToRun)
)

process.MessageLogger.destinations = ['cout', 'cerr']
process.MessageLogger.cerr.FwkReport.reportEvery = 1
process.options   = cms.untracked.PSet( wantSummary = cms.untracked.bool(False) )

#process.options = cms.untracked.PSet( SkipEvent = cms.untracked.vstring('ProductNotFound')
#)
process.source = cms.Source("PoolSource", fileNames = cms.untracked.vstring(
#       '/store/user/lnujj/PatTuples_8TeV_53X/ajkumar/W4JetsToLNu_TuneZ2Star_8TeV-madgraph/SQWaT_PAT_53X_Summer12_v1/829f288d768dd564418efaaf3a8ab9aa/pat_53x_test_v03_1003_0_YFd.root',
#    '/store/user/lnujj/PatTuples_8TeV_53X-v1/jdamgov/WJetsToLNu_TuneZ2Star_8TeV-madgraph-tarball/SQWaT_PAT_53X_Summer12_v1/829f288d768dd564418efaaf3a8ab9aa/pat_53x_test_v03_995_1_wBa.root'
    '/store/user/lnujj/PatTuples_8TeV_53X-v1/jdamgov/SingleElectron/SQWaT_PAT_53X_Run2012A-recover-06Aug2012-v1/3e4086321697e2c39c90dad08848274b/pat_53x_test_v03_data_9_1_IaF.root'
) )




##-------- Electron events of interest --------
process.HLTEle =cms.EDFilter("HLTHighLevel",
     TriggerResultsTag = cms.InputTag("TriggerResults","","HLT"),
     HLTPaths = cms.vstring('HLT_Ele27_*','HLT_Ele32_*'),
     eventSetupPathsKey = cms.string(''),
     andOr = cms.bool(True), #----- True = OR, False = AND between the HLTPaths
     throw = cms.bool(False) # throw exception on unknown path names
)

process.primaryVertex.src = cms.InputTag("goodOfflinePrimaryVertices");
process.primaryVertex.cut = cms.string(" ");

##########################################
## Filter to require at least two jets in the event
process.RequireTwoJetsORboostedV = cms.EDFilter("JetsORboostedV",
    minNumber = cms.untracked.int32(2),
    maxNumber = cms.untracked.int32(100),
    srcJets = cms.InputTag("ak5PFJetsLooseIdAll"),
    srcVectorBoson = cms.InputTag("bestWToEnu"),
    minVpt = cms.untracked.double(100.),
    minNumberPhotons = cms.untracked.int32(0)
)
process.RequireTwoJetsORboostedVStep = process.AllPassFilter.clone()


##-------- Save V+jets trees --------
process.VplusJets = cms.EDAnalyzer("VplusJetsAnalysis", 
    jetType = cms.string("PF"),
  #  srcPFCor = cms.InputTag("selectedPatJetsPFlow"),
    srcPFCor = cms.InputTag("ak5PFJetsLooseId"),
    srcPhoton = cms.InputTag("photons"),
    IsoValPhoton = cms.VInputTag(cms.InputTag('phoPFIso:chIsoForGsfEle'),
                                 cms.InputTag('phoPFIso:phIsoForGsfEle'),
                                 cms.InputTag('phoPFIso:nhIsoForGsfEle'),
                                                           ),
    srcPFCorVBFTag = cms.InputTag("ak5PFJetsLooseIdVBFTag"), 
    srcVectorBoson = cms.InputTag("bestWToEnu"),
    VBosonType     = cms.string('W'),
    LeptonType     = cms.string('electron'),                          
    TreeName    = cms.string('WJet'),
    srcPrimaryVertex = cms.InputTag("goodOfflinePrimaryVertices"),                               
    runningOverMC = cms.bool(isMC),			
    runningOverAOD = cms.bool(False),			
    srcMet = cms.InputTag("patMetShiftCorrected"),
    srcMetMVA = cms.InputTag("pfMEtMVA"),
    srcGen  = cms.InputTag("ak5GenJets"),
    srcElectrons  = cms.InputTag("selectedPatElectronsPFlow"),
    srcBeamSpot  = cms.InputTag("offlineBeamSpot"),
    srcCaloMet  = cms.InputTag("patMETs"),
    srcgenMet  = cms.InputTag("genMetTrue"),
    srcGenParticles  = cms.InputTag("genParticles"),
    srcTcMet    = cms.InputTag("patMETsAK5TC"),
    srcJetsforRho = cms.string("kt6PFJetsPFlow"),                               
    srcJetsforRho_lepIso = cms.string("kt6PFJetsForIsolation"),       
    srcJetsforRhoCHS = cms.string("kt6PFJetsChsPFlow"),
    srcJetsforRho_lepIsoCHS = cms.string("kt6PFJetsChsForIsolationPFlow"),

    applyJECToGroomedJets=cms.bool(True),
    doGroomedAK5 = cms.bool(True),
    doGroomedAK7 = cms.bool(True),
    doGroomedAK8 = cms.bool(False),
    doGroomedCA8 = cms.bool(True),
    doGroomedCA12 = cms.bool(False)
)


if isMC:
    process.VplusJets.JEC_GlobalTag_forGroomedJet = cms.string("START53_V15")
else:
    process.VplusJets.JEC_GlobalTag_forGroomedJet = cms.string("FT_53_V10_AN3")



process.TFileService = cms.Service(
    "TFileService", 
    fileName = cms.string( OutputFileName ),
    closeFileFast = cms.untracked.bool(False)
)

#process.QGTagger.srcJets = cms.InputTag('ak5PFJets')
process.QGTagger.srcJets = cms.InputTag('selectedPatJetsPFlow')
process.QGTagger.isPatJet  = cms.untracked.bool(True)
process.QGTagger.useCHS  = cms.untracked.bool(True)
#process.QGTagger.useCHS  = cms.untracked.bool(False)
#process.QGTagger.jec     = cms.untracked.string('ak5PFL1FastL2L3')
process.QGTagger.srcRho     = cms.InputTag('kt6PFJetsPFlow','rho')
process.QGTagger.srcRhoIso     = cms.InputTag('kt6PFJetsPFlow','rho')
#process.QGTagger.srcRhoIso1 = process.QGTagger.srcRhoIso.clone()
#process.QGTagger.srcRhoIso1 = process.QGTagger.srcRhoIso1(rParam = 0.6, doRhoFastjet = True )
#process.QGTagger.srcRhoIso1 = process.QGTagger.srcRhoIso1.Rho_EtaMax = cms.double(2.5)
#process.QGTagger.srcRhoIso     = cms.InputTag('kt6PFJetsPFlow','rho')


##
## MET shift correction on the fly
##
#from PhysicsTools.PatAlgos.tools.metTools import addPfMET

process.load("JetMETCorrections/Type1MET/pfMETsysShiftCorrections_cfi")
process.pfMEtSysShiftCorr.src = cms.InputTag('patMETsPFlow')
process.pfMEtSysShiftCorr.srcMEt = cms.InputTag('patMETsPFlow')
process.pfMEtSysShiftCorr.srcJets = cms.InputTag('selectedPatJetsPFlow')

if isMC:
# pfMEtSysShiftCorrParameters_2012runAplusBvsNvtx_mc
  process.pfMEtSysShiftCorr.parameter = cms.PSet(
    numJetsMin = cms.int32(-1),
    numJetsMax = cms.int32(-1),
    px = cms.string("+2.22335e-02 - 6.59183e-02*Nvtx"),
    py = cms.string("+1.52720e-01 - 1.28052e-01*Nvtx")
  )
else:
# pfMEtSysShiftCorrParameters_2012runAplusBvsNvtx_data
  process.pfMEtSysShiftCorr.parameter = cms.PSet(
    numJetsMin = cms.int32(-1),
    numJetsMax = cms.int32(-1),
    px = cms.string("+1.68804e-01 + 3.37139e-01*Nvtx"),
    py = cms.string("-1.72555e-01 - 1.79594e-01*Nvtx")
  )

process.patMetShiftCorrected = cms.EDProducer("CorrectedPATMETProducer",
    src = cms.InputTag('patMETsPFlow'),
    applyType1Corrections = cms.bool(True),
    srcType1Corrections = cms.VInputTag(
        cms.InputTag('pfMEtSysShiftCorr')
    ),
    applyType2Corrections = cms.bool(False)
)

process.myseq = cms.Sequence(
    process.pfMEtSysShiftCorrSequence *
    process.patMetShiftCorrected *
    process.TrackVtxPath *
    process.HLTEle *
    process.WPath *
    process.GenJetPath *
##    process.btagging * 
    process.TagJetPath *
    process.PFJetPath *
    process.RequireTwoJetsORboostedV *
    process.RequireTwoJetsORboostedVStep
    )

if isMC:
    process.myseq.remove ( process.noscraping)
    process.myseq.remove ( process.HBHENoiseFilter)
    process.myseq.remove ( process.HLTEle)
else:
    process.myseq.remove ( process.noscraping)
    process.myseq.remove ( process.HBHENoiseFilter)
    process.myseq.remove ( process.GenJetPath)
    process.myseq.remove ( process.TagJetPath)

process.QuarkGluonTagger.remove( process.kt6PFJetsQG )
process.QuarkGluonTagger.remove( process.kt6PFJetsIsoQG )

##---- if do not want to require >= 2 jets then disable that filter ---
##process.myseq.remove ( process.RequireTwoJets)  

#process.outpath.remove(process.out)
process.p = cms.Path( process.myseq * process.goodOfflinePrimaryVerticesQG * process.QuarkGluonTagger * process.VplusJets)
#process.p = cms.Path( process.myseq  * process.VplusJets)
