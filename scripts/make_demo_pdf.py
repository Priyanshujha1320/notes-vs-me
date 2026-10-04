from __future__ import annotations
"""Generate sample-notes.pdf — fake-but-realistic course notes for testing.

Run:  .venv/bin/python scripts/make_demo_pdf.py
"""
import fitz

SECTIONS = [
    ("Photosynthesis: an overview",
     "Photosynthesis is the process by which green plants, algae and some "
     "bacteria convert light energy into chemical energy stored in glucose. "
     "It takes place in chloroplasts, organelles containing the pigment "
     "chlorophyll, which absorbs mostly red and blue light and reflects "
     "green. The overall balanced equation is 6CO2 + 6H2O + light energy -> "
     "C6H12O6 + 6O2. Photosynthesis occurs in two connected stages: the "
     "light-dependent reactions in the thylakoid membranes, and the Calvin "
     "cycle in the stroma."),

    ("Light-dependent reactions",
     "The light-dependent reactions occur in the thylakoid membranes. "
     "Photosystem II absorbs photons, exciting electrons that travel down "
     "the electron transport chain toward photosystem I. Water is split in a "
     "process called photolysis, releasing oxygen as a by-product and "
     "supplying replacement electrons. The energy released as electrons move "
     "down the chain pumps protons into the thylakoid lumen, creating a "
     "proton gradient. ATP synthase uses this gradient to produce ATP in a "
     "process called chemiosmosis, and NADP+ is reduced to NADPH."),

    ("The Calvin cycle",
     "The Calvin cycle, also called the light-independent stage, takes place "
     "in the stroma of the chloroplast. It uses the ATP and NADPH produced in "
     "the light-dependent reactions to fix carbon dioxide into organic "
     "molecules. The enzyme RuBisCO catalyses the reaction of CO2 with "
     "ribulose bisphosphate (RuBP), a five-carbon sugar, producing two "
     "molecules of glycerate 3-phosphate (GP). GP is then reduced to "
     "triose phosphate (TP) using NADPH and ATP. Some TP is used to regenerate "
     "RuBP; the rest is used to synthesise glucose and other carbohydrates."),

    ("Limiting factors",
     "The rate of photosynthesis is limited by light intensity, carbon "
     "dioxide concentration and temperature. Light intensity increases the "
     "rate until saturation, when another factor becomes limiting. CO2 "
     "concentration is often the limiting factor in bright daylight. "
     "Temperature affects the rate because the Calvin cycle is catalysed by "
     "enzymes; above roughly 40 degrees Celsius, enzymes begin to denature "
     "and the rate falls sharply. Farmers exploit these factors in "
     "greenhouses, raising CO2 levels and controlling temperature to "
     "increase crop yields."),

    ("C4 and CAM adaptations",
     "Some plants have evolved adaptations to hot, dry climates. C4 plants "
     "such as maize separate carbon fixation from the Calvin cycle in space: "
     "CO2 is first fixed into a four-carbon compound in mesophyll cells, then "
     "transported to bundle-sheath cells where the Calvin cycle runs at high "
     "CO2 concentration. This reduces wasteful photorespiration. CAM plants "
     "such as cacti separate the two stages in time: stomata open at night to "
     "fix CO2 into organic acids, and the Calvin cycle runs during the day "
     "with stomata closed, minimising water loss."),
]


def main() -> None:
    doc = fitz.open()
    page = doc.new_page()
    y = 72
    title = "BIO 201 — Plant Physiology: Photosynthesis (Course Notes)"
    page.insert_text((72, y), title, fontsize=14, fontname="hebo")
    y += 30
    for heading, body in SECTIONS:
        if y > 700:
            page = doc.new_page()
            y = 72
        page.insert_text((72, y), heading, fontsize=11, fontname="hebo")
        y += 16
        # naive word wrap at ~95 chars
        import textwrap
        for line in textwrap.wrap(body, width=95):
            page.insert_text((72, y), line, fontsize=10, fontname="helv")
            y += 13
        y += 14
    doc.save("sample-notes.pdf")
    print("wrote sample-notes.pdf")


if __name__ == "__main__":
    main()
