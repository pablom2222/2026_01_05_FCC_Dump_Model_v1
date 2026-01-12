#include <iostream>

#include "TFile.h"
#include "TTree.h"
#include "TTreeReader.h"
#include "TTreeReaderValue.h"
#include "TSystem.h"

// BDSIM
#include "BDSOutputROOTEventSampler.hh"
#include "BDSOutputROOTEventSamplerLinkDef.hh"

using namespace std;

void CountSamplerParticles(const char* filename)
{
    gSystem->Load("librebdsim");
    gSystem->Load("libbdsimRootEvent");

    TFile* f = TFile::Open(filename);
    if (!f || f->IsZombie()) {
        cerr << "ERROR: Cannot open file " << filename << endl;
        return;
    }

    cout << "Opened ROOT file: " << filename << endl;

    TTree* eventTree = (TTree*)f->Get("Event");
    if (!eventTree) {
        cerr << "ERROR: No Event tree found!" << endl;
        f->ls();
        return;
    }

    TTreeReader reader(eventTree);

    TTreeReaderValue<BDSOutputROOTEventSampler<float>>
      sampler(reader, "front_window_sampler.");

    int nEvents = 0;
    int nCross  = 0;
    int nMiss   = 0;

    // Loop over events
    while (reader.Next()) {
        nEvents++;

        bool crossed = false;

        // Loop over hits in this event
        for (size_t i = 0; i < sampler->x.size(); i++) {

            // Primary photon only
            if (sampler->partID[i] == 22 && sampler->parentID[i] == 0) {
                crossed = true;
                break;
            }
        }

        if (crossed)
            nCross++;
        else
            nMiss++;
    }

    cout << "\n===== SAMPLER RESULT =====" << endl;
    cout << "Total events           : " << nEvents << endl;
    cout << "Primary photons crossed: " << nCross << endl;
    cout << "Primary photons missed : " << nMiss << endl;

    if (nEvents > 0) {
        cout << "Fraction crossed       : "
             << double(nCross) / double(nEvents) << endl;
    }

    cout << "=========================\n" << endl;

    f->Close();
}