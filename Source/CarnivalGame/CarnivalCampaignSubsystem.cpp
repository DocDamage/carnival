// Copyright CarnivalMetaHuman. All Rights Reserved.
#include "CarnivalCampaignSubsystem.h"
#include "CarnivalMissionSubsystem.h"
#include "Engine/GameInstance.h"
#include "Algo/AnyOf.h"

const TArray<FCarnivalCampaignStation>& UCarnivalCampaignSubsystem::Stations()
{
	// These stable IDs are also the persistent journal order. Append or migrate IDs;
	// never reorder a released campaign without a save migration.
	static const TArray<FCarnivalCampaignStation> Data = {
		{TEXT("hospital_reception"), TEXT("After the music"), TEXT("Hospital reception"), TEXT("Visit hospital reception and ask where Eli is resting."), TEXT("Eli is safe. He left permission to read his maintenance notes; his disappearance began with a signal from below the Carnival."), TEXT("VisitingPass"), TEXT("Eli's visiting pass"), TEXT("")},
		{TEXT("hospital_ward"), TEXT("After the music"), TEXT("Hospital ward"), TEXT("Take the visiting pass to Eli's ward and read his account."), TEXT("The music box repeats a four-note service signal. Eli traced it through the wetlands before getting lost in the mansion."), TEXT("EliAccount"), TEXT("Eli's account"), TEXT("")},
		{TEXT("hospital_records"), TEXT("After the music"), TEXT("Hospital records room"), TEXT("Compare Eli's notes with the hospital utility chart."), TEXT("The chart connects the hospital, slums and Carnival to an abandoned tide-powered network. A field marker survives in the wetlands."), TEXT("UtilityChart"), TEXT("Hospital utility chart"), TEXT("")},
		{TEXT("wetlands_markers"), TEXT("The broken line"), TEXT("Wetlands"), TEXT("Follow the three wetland survey markers in order: 1, 2, 3."), TEXT("The field survey leads to the railroad bridge service cabinet. The old crossing remains a walking route."), TEXT("SurveyRecord"), TEXT("Wetland survey record"), TEXT("123")},
		{TEXT("bridge_relay"), TEXT("The broken line"), TEXT("Railroad bridge"), TEXT("Restore the bridge service relay: switch 2, then 3, then 1."), TEXT("The relay identifies a disconnected feeder in the industrial slums. The crossing is clear for the return journey."), TEXT("FeederTag"), TEXT("Bridge feeder tag"), TEXT("231")},
		{TEXT("slums_workshop"), TEXT("The broken line"), TEXT("Industrial slums"), TEXT("Match the feeder tag to the workshop repair ledger."), TEXT("The ledger records that network equipment was moved to the prison archive after the facility closed."), TEXT("RepairLedger"), TEXT("Workshop repair ledger"), TEXT("")},
		{TEXT("prison_archive"), TEXT("Beneath the surface"), TEXT("Prison"), TEXT("Use the repair ledger to find the prison archive transfer entry."), TEXT("The prison paintings conceal the archivist's location index. The index points to Research Lab A; no captive needs rescuing."), TEXT("LabPermit"), TEXT("Research access record"), TEXT("")},
		{TEXT("lab_a_calibration"), TEXT("Beneath the surface"), TEXT("Research Lab A"), TEXT("Calibrate Lab A's tide receiver: switch 2, then 1, then 3."), TEXT("The receiver separates the music-box signal from background noise. Lab B holds the mapped outfall and a remote relay model."), TEXT("ReceiverSample"), TEXT("Calibrated receiver sample"), TEXT("213")},
		{TEXT("lab_b_chart"), TEXT("Beneath the surface"), TEXT("Research Lab B"), TEXT("Compare the receiver sample with Lab B's wall chart."), TEXT("The chart links the sewer outfall to the North and East Docks. A shipwreck carries the missing tide-core manifest."), TEXT("OutfallChart"), TEXT("Sewer outfall chart"), TEXT("")},
		{TEXT("sewer_route"), TEXT("The tide road"), TEXT("Sewers"), TEXT("Inspect the three outfall markers in order: 1, 2, 3."), TEXT("The marked outfall reaches the North Docks service landing. Watercraft access must use the signed shore route."), TEXT("LandingRecord"), TEXT("Outfall landing record"), TEXT("123")},
		{TEXT("north_docks_manifest"), TEXT("The tide road"), TEXT("North Docks"), TEXT("Check the North Docks shipping register."), TEXT("The tide-core shipment was diverted to the East Docks. The register identifies its wreck and the recovery landing."), TEXT("ShippingRegister"), TEXT("North Docks shipping register"), TEXT("")},
		{TEXT("east_docks_dispatch"), TEXT("The tide road"), TEXT("East Docks"), TEXT("Match the shipping register at the East Docks dispatch desk."), TEXT("The dispatch record marks a safe approach to the shipwreck. Keep the manifest aboard for the return trip."), TEXT("WreckLocator"), TEXT("Shipwreck locator"), TEXT("")},
		{TEXT("shipwreck_manifest"), TEXT("The tide road"), TEXT("Shipwreck"), TEXT("Recover the sealed manifest from the shipwreck."), TEXT("The manifest records a tide core sheltered in the Atlantis ruins. Its cradle must be released in sequence."), TEXT("TideManifest"), TEXT("Sealed tide-core manifest"), TEXT("")},
		{TEXT("atlantis_cradle"), TEXT("The quiet engine"), TEXT("Atlantis Ruins"), TEXT("Release the Atlantis cradle: switch 3, then 2, then 1."), TEXT("The recovered core is inert and safe to carry. Lab B's remote relay can calibrate it."), TEXT("TideCore"), TEXT("Recovered tide core"), TEXT("321")},
		{TEXT("lab_b_remote"), TEXT("The quiet engine"), TEXT("Research Lab B"), TEXT("Calibrate the tide core at the remote relay: switch 1, then 2, then 3."), TEXT("The relay confirms a harmless resonance in the music box. Return to the mansion to close the old receiver."), TEXT("RemoteAuthorization"), TEXT("Remote relay authorization"), TEXT("123")},
		{TEXT("mansion_receiver"), TEXT("Home again"), TEXT("Mansion"), TEXT("Close the mansion receiver: switch 3, then 1, then 2."), TEXT("The music box falls silent. The doll encounter was a mechanical alarm; it never harmed Eli or the player."), TEXT("RestorationSeal"), TEXT("Network restoration seal"), TEXT("312")},
		{TEXT("carnival_restoration"), TEXT("Home again"), TEXT("Carnival"), TEXT("Return the restoration seal to the Carnival service board."), TEXT("The network is stable, Eli is recovering, and the Carnival remains open. Explore, ride, build and replay the investigation."), TEXT("CarnivalKeepsake"), TEXT("Carnival restoration keepsake"), TEXT("")}
	};
	return Data;
}

namespace
{
	// Version-2 saves counted progress through this 22-station order, which included
	// Town, Lighthouse, Castle, Arena and Mars before they left the demo scope.
	const TCHAR* const Version2Order[][2] = {
		{TEXT("hospital_reception"), TEXT("VisitingPass")}, {TEXT("hospital_ward"), TEXT("EliAccount")},
		{TEXT("hospital_records"), TEXT("UtilityChart")}, {TEXT("wetlands_markers"), TEXT("SurveyRecord")},
		{TEXT("bridge_relay"), TEXT("FeederTag")}, {TEXT("slums_workshop"), TEXT("RepairLedger")},
		{TEXT("town_archive"), TEXT("KeeperCode")}, {TEXT("lighthouse_beacon"), TEXT("ClockSeal")},
		{TEXT("castle_clock"), TEXT("TransferEntry")}, {TEXT("prison_archive"), TEXT("LabPermit")},
		{TEXT("lab_a_calibration"), TEXT("ReceiverSample")}, {TEXT("lab_b_chart"), TEXT("OutfallChart")},
		{TEXT("sewer_route"), TEXT("LandingRecord")}, {TEXT("north_docks_manifest"), TEXT("ShippingRegister")},
		{TEXT("east_docks_dispatch"), TEXT("WreckLocator")}, {TEXT("shipwreck_manifest"), TEXT("TideManifest")},
		{TEXT("atlantis_cradle"), TEXT("TideCore")}, {TEXT("arena_circuit"), TEXT("CoreCalibration")},
		{TEXT("lab_b_remote"), TEXT("RemoteAuthorization")}, {TEXT("mars_relay"), TEXT("ResonanceRecord")},
		{TEXT("mansion_receiver"), TEXT("RestorationSeal")}, {TEXT("carnival_restoration"), TEXT("CarnivalKeepsake")}};
}

bool UCarnivalCampaignSubsystem::MigrateVersion2(const FCarnivalCampaignSnapshot& Legacy, FCarnivalCampaignSnapshot& Out)
{
	constexpr int32 LegacyCount = UE_ARRAY_COUNT(Version2Order);
	if (Legacy.CompletedStations < 0 || Legacy.CompletedStations > LegacyCount) return false;
	// Completed stations that remain in scope keep their progress; removed ones are skipped.
	int32 Kept = 0;
	for (int32 Index = 0; Index < Legacy.CompletedStations; ++Index)
		Kept += Stations().ContainsByPredicate([Index](const auto& Station) { return Station.Id == Version2Order[Index][0]; });
	const FName LegacyExpected = Legacy.CompletedStations > 0 ? FName(Version2Order[Legacy.CompletedStations - 1][1]) : NAME_None;
	FCarnivalCampaignSnapshot Next = Legacy;
	Next.CompletedStations = Kept;
	int32 QuestStacks = 0;
	for (int32 Index = Next.Inventory.Num() - 1; Index >= 0; --Index)
	{
		const FName Item = Next.Inventory[Index].Item;
		const bool bLegacyQuest = Algo::AnyOf(Version2Order, [Item](const auto& Row) { return Item == Row[1]; });
		if (!bLegacyQuest) continue;
		if (Item != LegacyExpected || Next.Inventory[Index].Count != 1) return false;
		++QuestStacks; Next.Inventory.RemoveAt(Index);
	}
	if (QuestStacks != (LegacyExpected.IsNone() ? 0 : 1)) return false;
	// A token from a removed station becomes the token the next kept station expects.
	if (Kept > 0) { auto& Token = Next.Inventory.AddDefaulted_GetRef(); Token.Item = Stations()[Kept - 1].Reward; Token.Count = 1; }
	if (!IsValidSnapshot(Next)) return false;
	Out = MoveTemp(Next);
	return true;
}

bool UCarnivalCampaignSubsystem::IsQuestItem(FName Item)
{
	return Stations().ContainsByPredicate([Item](const auto& Station) { return Station.Reward == Item; });
}

int32 UCarnivalCampaignSubsystem::ItemLimit(FName Item)
{
	if (IsQuestItem(Item)) return 1;
	if (Item == TEXT("Tickets")) return 9999;
	if (Item == TEXT("Timber") || Item == TEXT("Steel")) return 20;
	if (Item == TEXT("RepairKit")) return 3;
	if (Item == TEXT("Fuse")) return 5;
	if (Item == TEXT("Rope")) return 2;
	if (Item == TEXT("MedicalKit")) return 3;
	if (Item == TEXT("Battery")) return 4;
	return 0;
}

FString UCarnivalCampaignSubsystem::ItemLabel(FName Item)
{
	for (const auto& Station : Stations()) if (Station.Reward == Item) return Station.RewardLabel;
	if (Item == TEXT("RepairKit")) return TEXT("Repair kits");
	return Item.ToString();
}

bool UCarnivalCampaignSubsystem::IsValidSnapshot(const FCarnivalCampaignSnapshot& Snapshot)
{
	if (Snapshot.CompletedStations < 0 || Snapshot.CompletedStations > Stations().Num()
		|| (!Snapshot.bUnlocked && Snapshot.CompletedStations != 0) || Snapshot.Inventory.Num() > SupplySlots + 1) return false;
	TSet<FName> Seen;
	int32 SupplyCount = 0, QuestCount = 0;
	const FName Expected = Snapshot.CompletedStations > 0 ? Stations()[Snapshot.CompletedStations - 1].Reward : NAME_None;
	for (const auto& Stack : Snapshot.Inventory)
	{
		if (Stack.Item.IsNone() || Seen.Contains(Stack.Item) || Stack.Count < 1 || Stack.Count > ItemLimit(Stack.Item)) return false;
		Seen.Add(Stack.Item);
		if (IsQuestItem(Stack.Item)) { if (Stack.Item != Expected) return false; ++QuestCount; }
		else ++SupplyCount;
	}
	return SupplyCount <= SupplySlots && QuestCount == (Expected.IsNone() ? 0 : 1);
}

bool UCarnivalCampaignSubsystem::Restore(const FCarnivalCampaignSnapshot& Snapshot)
{
	if (!IsValidSnapshot(Snapshot)) { LastResult = TEXT("Campaign or inventory data is invalid. Current progress was kept."); return false; }
	State = Snapshot;
	SequencePosition = 0;
	LastResult.Reset();
	return true;
}

bool UCarnivalCampaignSubsystem::HasRescuedWorker() const
{
	const auto* Mission = GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>();
	return Mission && Mission->IsMissionComplete();
}

bool UCarnivalCampaignSubsystem::IsComplete() const { return State.CompletedStations == Stations().Num(); }

bool UCarnivalCampaignSubsystem::CanUseStation(FName Station) const
{
	return !IsComplete() && (State.bUnlocked || HasRescuedWorker()) && Stations()[State.CompletedStations].Id == Station;
}

FText UCarnivalCampaignSubsystem::GetObjective() const
{
	if (!State.bUnlocked && !HasRescuedWorker()) return FText::GetEmpty();
	if (IsComplete()) return FText::FromString(TEXT("The signal network is restored. The Carnival is open for free play."));
	const auto& Station = Stations()[State.CompletedStations];
	return FText::FromString(Station.Location + TEXT(": ") + Station.Objective);
}

int32 UCarnivalCampaignSubsystem::GetItemCount(FName Item) const
{
	const auto* Mission = GetGameInstance()->GetSubsystem<UCarnivalMissionSubsystem>();
	if (Mission)
	{
		if (Item == TEXT("WetGlove")) return Mission->bFoundFoyerGlove ? 1 : 0;
		if (Item == TEXT("ServiceKey") || Item == TEXT("StudyLog")) return Mission->bHasServiceKey ? 1 : 0;
		if (Item == TEXT("MusicBox")) return Mission->bRecoveredMusicBox ? 1 : 0;
	}
	for (const auto& Stack : State.Inventory) if (Stack.Item == Item) return Stack.Count;
	return 0;
}

bool UCarnivalCampaignSubsystem::GrantSupply(FName Item, int32 Count)
{
	const int32 Limit = ItemLimit(Item), Previous = GetItemCount(Item);
	if (IsQuestItem(Item) || Count <= 0 || Limit <= 0 || Count > Limit - Previous)
	{ LastResult = TEXT("This item cannot be added, or its stack is full."); return false; }
	FCarnivalCampaignSnapshot Next = State;
	if (Previous > 0) { for (auto& Stack : Next.Inventory) if (Stack.Item == Item) Stack.Count += Count; }
	else { auto& Stack = Next.Inventory.AddDefaulted_GetRef(); Stack.Item = Item; Stack.Count = Count; }
	if (!IsValidSnapshot(Next)) { LastResult = TEXT("The supply bag is full."); return false; }
	State = MoveTemp(Next); LastResult = TEXT("Supplies added."); return true;
}

bool UCarnivalCampaignSubsystem::SpendSupply(FName Item, int32 Count)
{
	if (IsQuestItem(Item) || Count <= 0 || GetItemCount(Item) < Count)
	{ LastResult = TEXT("You do not have enough of this supply."); return false; }
	for (auto& Stack : State.Inventory) if (Stack.Item == Item) { Stack.Count -= Count; break; }
	State.Inventory.RemoveAll([](const auto& Stack) { return Stack.Count == 0; });
	LastResult = TEXT("Supplies used."); return true;
}

bool UCarnivalCampaignSubsystem::UseStation(FName StationId, int32 Action)
{
	if (!CanUseStation(StationId)) { LastResult = TEXT("Follow the current journal objective first."); return false; }
	const auto& Station = Stations()[State.CompletedStations];
	if (State.CompletedStations > 0 && GetItemCount(Stations()[State.CompletedStations - 1].Reward) != 1)
	{ LastResult = TEXT("The required quest item is unavailable. Current progress was kept."); return false; }
	if (!Station.Sequence.IsEmpty())
	{
		if (Action < 1 || Action > 3) { LastResult = TEXT("Choose one of the three marked controls."); return false; }
		if (Action != Station.Sequence[SequencePosition] - TEXT('0'))
		{ SequencePosition = 0; LastResult = TEXT("That order did not match. Start the sequence again; no items were lost."); return false; }
		++SequencePosition;
		if (SequencePosition < Station.Sequence.Len())
		{ LastResult = FString::Printf(TEXT("Step %d of %d accepted."), SequencePosition, Station.Sequence.Len()); return true; }
	}
	else if (Action != 0) { LastResult = TEXT("Inspect this station to continue."); return false; }
	FCarnivalCampaignSnapshot Next = State;
	Next.Inventory.RemoveAll([](const auto& Stack) { return IsQuestItem(Stack.Item); });
	auto& Reward = Next.Inventory.AddDefaulted_GetRef(); Reward.Item = Station.Reward; Reward.Count = 1;
	++Next.CompletedStations; Next.bUnlocked = true;
	if (!IsValidSnapshot(Next)) { SequencePosition = 0; LastResult = TEXT("The exchange could not be completed. Current progress was kept."); return false; }
	State = MoveTemp(Next); SequencePosition = 0; LastResult = Station.Resolution; return true;
}

TArray<FString> UCarnivalCampaignSubsystem::GetInventoryLines() const
{
	TArray<FString> Lines; int32 Supplies = 0;
	for (const auto& Stack : State.Inventory) if (!IsQuestItem(Stack.Item)) ++Supplies;
	Lines.Add(FString::Printf(TEXT("Supplies: %d / %d slots. Quest items have reserved storage."), Supplies, SupplySlots));
	// Opening-story items are derived from the original mission state, whose
	// replay/save restoration remains the authority; avoid a second divergent copy.
	if (GetItemCount(TEXT("WetGlove"))) Lines.Add(TEXT("Investigation - wet work glove"));
	if (GetItemCount(TEXT("StudyLog"))) Lines.Add(TEXT("Investigation - study maintenance log"));
	if (GetItemCount(TEXT("ServiceKey"))) Lines.Add(TEXT("Investigation - music-room service key"));
	if (GetItemCount(TEXT("MusicBox"))) Lines.Add(TEXT("Investigation - recovered music box"));
	for (const auto& Stack : State.Inventory) Lines.Add(FString::Printf(TEXT("%s%s: %d / %d"), IsQuestItem(Stack.Item) ? TEXT("Quest - ") : TEXT(""), *ItemLabel(Stack.Item), Stack.Count, ItemLimit(Stack.Item)));
	if (Lines.Num() == 1) Lines.Add(TEXT("Your bag is empty."));
	return Lines;
}

TArray<FString> UCarnivalCampaignSubsystem::GetJournalLines() const
{
	TArray<FString> Lines;
	if (!State.bUnlocked && !HasRescuedWorker()) Lines.Add(TEXT("Rescue Eli and return to the Carnival to begin the signal investigation."));
	else Lines.Add(GetObjective().ToString());
	for (int32 Index = State.CompletedStations - 1; Index >= 0; --Index)
		Lines.Add(Stations()[Index].Location + TEXT(": ") + Stations()[Index].Resolution);
	return Lines;
}
