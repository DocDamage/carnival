#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "Misc/ScopeExit.h"
#include "CarnivalCampaignSubsystem.h"
#include "CarnivalMissionSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCarnivalCampaignInventoryTest, "Carnival.Campaign.InventoryAndProgress",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCarnivalCampaignInventoryTest::RunTest(const FString&)
{
	auto* Instance = NewObject<UGameInstance>(GEngine); Instance->InitializeStandalone(TEXT("CampaignInventory"));
	auto* World = Instance->GetWorld();
	ON_SCOPE_EXIT { Instance->Shutdown(); World->DestroyWorld(false); GEngine->DestroyWorldContext(World); };
	auto* Campaign = Instance->GetSubsystem<UCarnivalCampaignSubsystem>();
	auto* Mission = Instance->GetSubsystem<UCarnivalMissionSubsystem>();
	TestFalse(TEXT("Sequel cannot start before Eli returns safely"), Campaign->UseStation(TEXT("hospital_reception"), 0));
	TestTrue(TEXT("Fill the supply bag"), Campaign->GrantSupply(TEXT("Tickets"), 9999)
		&& Campaign->GrantSupply(TEXT("Timber"), 20) && Campaign->GrantSupply(TEXT("Steel"), 20)
		&& Campaign->GrantSupply(TEXT("RepairKit"), 3) && Campaign->GrantSupply(TEXT("Fuse"), 5)
		&& Campaign->GrantSupply(TEXT("Rope"), 2) && Campaign->GrantSupply(TEXT("MedicalKit"), 3)
		&& Campaign->GrantSupply(TEXT("Battery"), 4));
	TestFalse(TEXT("Stack overflow rejects the whole grant"), Campaign->GrantSupply(TEXT("Tickets"), MAX_int32));
	TestEqual(TEXT("Overflow kept the original stack"), Campaign->GetItemCount(TEXT("Tickets")), 9999);
	TestFalse(TEXT("Unknown items cannot enter the bag"), Campaign->GrantSupply(TEXT("Unknown"), 1));
	TestFalse(TEXT("Quest items cannot be minted by a supply grant"), Campaign->GrantSupply(TEXT("TideCore"), 1));
	TestFalse(TEXT("Negative spending cannot mint supplies"), Campaign->SpendSupply(TEXT("Steel"), -1));
	TestFalse(TEXT("Overspending is rejected"), Campaign->SpendSupply(TEXT("RepairKit"), 4));
	TestTrue(TEXT("Supply use removes an exhausted stack"), Campaign->SpendSupply(TEXT("RepairKit"), 3));
	TestEqual(TEXT("Exhausted supply is gone"), Campaign->GetItemCount(TEXT("RepairKit")), 0);
	TestTrue(TEXT("Refill last slot before quest acquisition"), Campaign->GrantSupply(TEXT("RepairKit"), 3));
	TestTrue(TEXT("Restore complete safe story for sequel"), Mission->RestoreSavedState(ECarnivalStoryMissionState::Complete));
	TestTrue(TEXT("Replay can begin before visiting the hospital"), Mission->BeginStoryMission());
	TestTrue(TEXT("Replay retains hospital access before the first sequel item"), Campaign->CanUseStation(TEXT("hospital_reception")));
	TestFalse(TEXT("Cannot skip ahead to the tide core"), Campaign->UseStation(TEXT("atlantis_cradle"), 3));
	TestTrue(TEXT("Quest acquisition succeeds with a full supply stack"), Campaign->UseStation(TEXT("hospital_reception"), 0));
	TestFalse(TEXT("Repeated acquisition cannot duplicate a quest reward"), Campaign->UseStation(TEXT("hospital_reception"), 0));
	TestFalse(TEXT("Quest tools cannot be discarded or spent as supplies"), Campaign->SpendSupply(TEXT("VisitingPass"), 1));
	TestTrue(TEXT("Ward exchanges the visiting pass"), Campaign->UseStation(TEXT("hospital_ward"), 0));
	TestEqual(TEXT("Prior pass is consumed only on success"), Campaign->GetItemCount(TEXT("VisitingPass")), 0);
	TestTrue(TEXT("Records resolve"), Campaign->UseStation(TEXT("hospital_records"), 0));
	TestTrue(TEXT("First route checkpoint"), Campaign->UseStation(TEXT("wetlands_markers"), 1));
	TestFalse(TEXT("Out of order route checkpoint resets without advancing"), Campaign->UseStation(TEXT("wetlands_markers"), 3));
	TestEqual(TEXT("Route mistake kept quest item"), Campaign->GetItemCount(TEXT("UtilityChart")), 1);
	TestTrue(TEXT("Restart first route checkpoint"), Campaign->UseStation(TEXT("wetlands_markers"), 1));
	const auto Partial = Campaign->Capture();
	TestTrue(TEXT("Partial puzzle snapshot restores"), Campaign->Restore(Partial));
	TestFalse(TEXT("Loading partial puzzle restarts its sequence"), Campaign->UseStation(TEXT("wetlands_markers"), 2));
	for (int32 Action : {1, 2, 3}) TestTrue(TEXT("Complete ordered route"), Campaign->UseStation(TEXT("wetlands_markers"), Action));
	auto Invalid = Campaign->Capture();
	const FCarnivalInventoryStack Duplicate = Invalid.Inventory.Last();
	Invalid.Inventory.Add(Duplicate);
	TestFalse(TEXT("Duplicate inventory entries reject restore"), Campaign->Restore(Invalid));
	TestEqual(TEXT("Rejected restore kept progress"), Campaign->Capture().CompletedStations, 4);
	Invalid = Campaign->Capture(); Invalid.Inventory.RemoveAll([](const auto& Stack) { return UCarnivalCampaignSubsystem::IsQuestItem(Stack.Item); });
	TestFalse(TEXT("Missing required quest item rejects a save snapshot"), UCarnivalCampaignSubsystem::IsValidSnapshot(Invalid));
	Invalid = Campaign->Capture(); Invalid.CompletedStations = MAX_int32;
	TestFalse(TEXT("Invalid station count rejects restore"), Campaign->Restore(Invalid));
	// Every authored station must be reachable, issue one quest reward and preserve
	// supplies. This exercises data integration rather than rendering/world placement.
	TSet<FName> StationIds;
	for (const auto& Station : UCarnivalCampaignSubsystem::Stations())
	{
		TestFalse(TEXT("Station ID is unique"), StationIds.Contains(Station.Id));
		StationIds.Add(Station.Id);
	}
	while (!Campaign->IsComplete())
	{
		const auto& Station = UCarnivalCampaignSubsystem::Stations()[Campaign->Capture().CompletedStations];
		if (Station.Sequence.IsEmpty()) TestTrue(TEXT("Evidence station resolves"), Campaign->UseStation(Station.Id, 0));
		else for (const TCHAR Action : Station.Sequence) TestTrue(TEXT("Ordered station resolves"), Campaign->UseStation(Station.Id, Action - TEXT('0')));
		TestTrue(TEXT("Each resulting snapshot validates"), UCarnivalCampaignSubsystem::IsValidSnapshot(Campaign->Capture()));
	}
	TestEqual(TEXT("Supplies survive the entire campaign"), Campaign->GetItemCount(TEXT("Tickets")), 9999);
	TestEqual(TEXT("Final keepsake is unique"), Campaign->GetItemCount(TEXT("CarnivalKeepsake")), 1);
	TestFalse(TEXT("Completed campaign cannot award its ending twice"), Campaign->UseStation(TEXT("carnival_restoration"), 0));
	Mission->RestoreSavedState(ECarnivalStoryMissionState::Complete);
	TestTrue(TEXT("Original investigation can be replayed"), Mission->BeginStoryMission());
	TestTrue(TEXT("Investigation replay preserves sequel and bag"), Campaign->IsComplete() && Campaign->GetItemCount(TEXT("Tickets")) == 9999);
	TestEqual(TEXT("Out-of-scope regions are not in the chain"), UCarnivalCampaignSubsystem::Stations().Num(), 17);
	// Version-2 saves used a 22-station chain through Town, Lighthouse, Castle, Arena and Mars.
	auto Legacy = [](int32 Completed, const TCHAR* Token)
	{
		FCarnivalCampaignSnapshot Snapshot; Snapshot.bUnlocked = true; Snapshot.CompletedStations = Completed;
		Snapshot.Inventory.Add({FName(TEXT("Timber")), 6});
		if (Token) Snapshot.Inventory.Add({FName(Token), 1});
		return Snapshot;
	};
	FCarnivalCampaignSnapshot Migrated;
	TestTrue(TEXT("Removed Town station migrates"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(7, TEXT("KeeperCode")), Migrated));
	TestTrue(TEXT("Town progress resumes at the prison with the slums ledger"), Migrated.CompletedStations == 6
		&& UCarnivalCampaignSubsystem::Stations()[6].Id == TEXT("prison_archive")
		&& Migrated.Inventory.ContainsByPredicate([](const auto& S) { return S.Item == TEXT("RepairLedger") && S.Count == 1; })
		&& Migrated.Inventory.ContainsByPredicate([](const auto& S) { return S.Item == TEXT("Timber") && S.Count == 6; }));
	TestTrue(TEXT("Removed Arena station migrates"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(18, TEXT("CoreCalibration")), Migrated));
	TestTrue(TEXT("Arena progress resumes at Lab B relay holding the core"), Migrated.CompletedStations == 14
		&& UCarnivalCampaignSubsystem::Stations()[14].Id == TEXT("lab_b_remote")
		&& Migrated.Inventory.ContainsByPredicate([](const auto& S) { return S.Item == TEXT("TideCore"); }));
	TestTrue(TEXT("Kept station progress migrates"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(10, TEXT("LabPermit")), Migrated) && Migrated.CompletedStations == 7);
	TestTrue(TEXT("Completed legacy campaign stays complete"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(22, TEXT("CarnivalKeepsake")), Migrated)
		&& Migrated.CompletedStations == UCarnivalCampaignSubsystem::Stations().Num());
	TestTrue(TEXT("Unstarted legacy sequel migrates"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(0, nullptr), Migrated) && Migrated.CompletedStations == 0);
	const auto Kept = Migrated;
	TestFalse(TEXT("Wrong legacy token rejects migration"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(7, TEXT("ClockSeal")), Migrated));
	TestFalse(TEXT("Missing legacy token rejects migration"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(7, nullptr), Migrated));
	TestFalse(TEXT("Out-of-range legacy count rejects migration"), UCarnivalCampaignSubsystem::MigrateVersion2(Legacy(23, nullptr), Migrated));
	TestTrue(TEXT("Rejected migration leaves output untouched"), Migrated.CompletedStations == Kept.CompletedStations && Migrated.Inventory.Num() == Kept.Inventory.Num());
	return true;
}
#endif
